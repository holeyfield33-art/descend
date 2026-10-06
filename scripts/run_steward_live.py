"""Frozen, explicitly approved WP6 workload; no retries or automatic resume."""
import argparse
import hashlib
import json
import os
import sqlite3
import time
from contextlib import closing
from pathlib import Path
from types import SimpleNamespace

from descend.controller.environment import load_controller_environment
from descend.controller.spend import SpendLedger, SpendExhausted
from descend.controller.token_factory import INFERENCE_BASE_URL
from descend.steward.act import ActStore, verify_proposal
from descend.steward.act_proxy import generate_proposal
from descend.steward.corpus import canonical, verify_manifest
from descend.steward.doctor import diagnose
from descend.steward.reviewer import review_with_nemotron
from descend.steward.scoring import blind_sheet, score_results, wilson
from scripts.plan_steward_live import plan


class RunBudget:
    """Additional conservative bound; underlying ledger enforces cumulative cap."""
    def __init__(self, ledger, stop_usd):
        self.ledger, self.limit, self.used, self.holds = ledger, round(stop_usd*1000000), 0, {}

    def reserve(self, run_id, amount):
        if self.used+amount > self.limit:
            raise SpendExhausted('Additional run reservation threshold reached')
        identifier = self.ledger.reserve(run_id, amount)
        self.holds[identifier] = amount
        self.used += amount
        return identifier

    def settle(self, identifier, charged, provider_id):
        # Preserve observed overruns even when the durable ledger raises.
        reserved = self.holds.pop(identifier)
        self.used += charged-reserved
        self.ledger.settle(identifier, charged, provider_id)


class RecordedClient:
    """Record payloads/response JSON, never credential headers or exception text."""
    def __init__(self, client, output, records=None):
        self.client, self.output = client, output
        self.records = [] if records is None else records
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self.create))

    def with_options(self, **options):
        return RecordedClient(self.client.with_options(**options), self.output, self.records)

    def create(self, **body):
        index = len(self.records)
        self.records.append(index)
        name = self.output / f'call-{index:03d}'
        request = {key:value for key,value in body.items() if key!='timeout'}
        (name.with_suffix('.request.json')).write_bytes(canonical(request))
        try:
            response = self.client.chat.completions.create(**body)
            (name.with_suffix('.response.json')).write_bytes(canonical(response.model_dump(mode='json')))
            return response
        except Exception as exc:
            (name.with_suffix('.error.json')).write_bytes(canonical({'error_type':type(exc).__name__,'automatic_retry':False}))
            raise


def check_plan(path, root=Path('.')):
    payload = json.loads(path.read_text(encoding='utf-8'))
    if payload != plan(root/'eval/v1'):
        raise ValueError('Plan differs from current predeclared configuration')
    if payload['status']!='PROPOSED_NOT_APPROVED_NOT_EXECUTED':
        raise ValueError('Unexpected plan status')
    for name, digest in payload['source_hashes'].items():
        if hashlib.sha256((root/name).read_bytes()).hexdigest()!=digest:
            raise ValueError('Plan source hash mismatch: '+name)
    manifest = verify_manifest(root/'eval/v1')
    if (root/'eval/v1/test-manifest.sha256').read_text().strip()!=payload['test_manifest_sha256']:
        raise ValueError('Plan corpus hash mismatch')
    tests = sorted(c['id'] for c in manifest['cases'] if c['split']=='test')
    if payload['primary_cases']!=tests or len(payload['repeat_cases'])!=10 or not set(payload['repeat_cases'])<=set(tests):
        raise ValueError('Plan case selection mismatch')
    if payload['total_call_cap']!=112 or payload['act_call_cap']!=8 or payload['stop_threshold_usd']!=6.4:
        raise ValueError('Unsupported plan budgets')
    return payload, manifest


def claim_plan(state, digest, corpus_identity=None):
    state.parent.mkdir(parents=True,exist_ok=True)
    with closing(sqlite3.connect(state)) as db, db:
        db.execute('CREATE TABLE IF NOT EXISTS runs (plan_hash TEXT PRIMARY KEY, status TEXT NOT NULL)')
        db.execute('CREATE TABLE IF NOT EXISTS splits (corpus_hash TEXT PRIMARY KEY, plan_hash TEXT NOT NULL)')
        if corpus_identity is not None:
            claimed=db.execute('INSERT OR IGNORE INTO splits VALUES (?,?)',(corpus_identity,digest))
            if claimed.rowcount!=1:
                raise RuntimeError('Frozen test split already claimed, including under another plan')
        cursor=db.execute('INSERT OR IGNORE INTO runs VALUES (?,?)',(digest,'claimed-no-resume'))
        if cursor.rowcount!=1:
            raise RuntimeError('This plan was already claimed; no automatic retry/resume')


def workload(payload, manifest, client, budget, output):
    results = {}
    variance = []
    acts = []
    cases = {c['id']:c for c in manifest['cases']}
    actions = ActStore(output/'acts.sqlite')
    halted = False
    act_count = 0
    acted_cases = set()
    candidates = []
    for model in payload['models']:
        primary = []
        for repeat, ids in [(0,payload['primary_cases']), (1,payload['repeat_cases']), (2,payload['repeat_cases'])]:
            for identifier in ids:
                directory = Path('eval/v1/cases')/identifier
                diff = (directory/'review.diff').read_text(encoding='utf-8')
                digest = hashlib.sha256(diff.encode()).hexdigest()
                snapshot = dict(status='ready', repo='seeded:'+identifier, sha=digest[:40], paths=['app.py'], diff=diff, diff_sha256=digest)
                row = {'case':identifier,'model':model,'repeat':repeat,'content':'',
                       'snapshot_identity':'Owned seeded diff hash; not a real Git commit',
                       'error':'NOT_RUN' if halted else None}
                if not halted:
                    started = time.monotonic()
                    try:
                        row.update(review_with_nemotron(snapshot,api_key='controller-client-injected',ledger=budget,client=client,model=model))
                        row['error'] = None
                    except Exception as exc:
                        row['error'] = type(exc).__name__
                        # Fail closed on any provider/usage/budget failure; preserve unrun cases.
                        halted = True
                    row['latency_seconds'] = time.monotonic()-started
                if repeat==0:
                    primary.append(row)
                else:
                    variance.append(row)
                # Evaluator-only label selects bounded TP/ambiguous bug cases;
                # labels, fix and generator test never enter the model request.
                if repeat==0 and not halted and len(candidates)<8 and identifier not in acted_cases and cases[identifier]['label']=='bug' and row.get('findings'):
                    acted_cases.add(identifier)
                    candidates.append((identifier,model,snapshot,row['findings'][0]))
                # Persist partial progress before the next consequential call.
                (output/'progress.json').write_bytes(canonical({'primary':results,'current_model':model,
                                                               'current_primary':primary,'variance':variance,'acts':acts,'halted':halted}))
        results[model] = primary
        arm = 'Super' if model==payload['models'][0] else 'Nano'
        (output/(arm+'.json')).write_bytes(canonical({'arm':arm,'results':primary}))
        scored_cases = [{**case,'diff':(Path('eval/v1/cases')/case['id']/'review.diff').read_text(encoding='utf-8')}
                        for case in manifest['cases'] if case['split']=='test']
        scores = score_results(scored_cases,primary)
        scores.update(arm=arm,split='test')
        (output/(arm+'-scores.json')).write_bytes(canonical(scores))
        sheet,mapping = blind_sheet(scores)
        (output/(arm+'-blind.json')).write_bytes(canonical(sheet))
        (output/(arm+'-mapping.json')).write_bytes(canonical(mapping))
    # Act errors cannot prevent completion of the primary model comparison.
    for identifier,model,snapshot,finding in candidates:
        if halted:
            acts.append({'case':identifier,'error_type':'NOT_RUN'})
            continue
        act_count += 1
        directory=Path('eval/v1/cases')/identifier
        started=time.monotonic()
        try:
            proposal=generate_proposal(snapshot,finding,(directory/'review/app.py').read_text(),
                                       store=actions,ledger=budget,client=client,finding_index=0,
                                       commit_cap=1,model=model)
            verified=verify_proposal(directory/'review',finding,proposal['raw'],output/'patches'/identifier,
                                     review_diff=snapshot['diff'],proposal_kind='live',identity={'repo':snapshot['repo'],
                                     'reviewed_commit':snapshot['sha'],'finding_index':0,'seeded_case':identifier,
                                     'test_manifest_sha256':payload['test_manifest_sha256']})
            actions.finish(snapshot['repo'],snapshot['sha'],0,verified)
            acts.append({'case':identifier,'proposal':proposal,'verification':verified,'latency_seconds':time.monotonic()-started})
        except Exception as exc:
            acts.append({'case':identifier,'error_type':type(exc).__name__})
            halted=True
        (output/'acts.json').write_bytes(canonical(acts))
    (output/'variance.json').write_bytes(canonical(variance))
    (output/'acts.json').write_bytes(canonical(acts))
    attempted=[row for row in acts if row.get('error_type')!='NOT_RUN']
    (output/'act-metrics.json').write_bytes(canonical({'verification':wilson(
        sum(row.get('verification',{}).get('classification')=='PATCH_VERIFIED' for row in attempted),len(attempted)),
        'denominator':'All attempted model act proposals, including errors; selected bug cases only',
        'selection_limitation':'First eligible distinct bug cases in Super-first order; not an unbiased patch-success estimate'}))
    return {'halted':halted,'review_rows':sum(len(rows) for rows in results.values())+len(variance),
            'act_attempts':act_count,'additional_accounted_upper_bound_usd':budget.used/1000000,
            'kind':'live','automatic_resume':False}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plan',type=Path,required=True)
    parser.add_argument('--check',action='store_true',help='Hash/config checks only; no environment/key/client reads')
    parser.add_argument('--approval',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--env-file',default='.env')
    args=parser.parse_args()
    payload,manifest=check_plan(args.plan)
    digest=hashlib.sha256(args.plan.read_bytes()).hexdigest()
    if args.check:
        print(json.dumps({'plan_sha256':digest,'hashes_valid':True,'provider_calls':0}))
        return
    if not args.approval or not args.output:
        parser.error('Written quantified approval and new output directory required')
    expected=f'APPROVE PLAN {digest} CAP_USD 8'
    if args.approval.read_text(encoding='utf-8').strip()!=expected:
        parser.error('Approval must name this exact plan hash and cap')
    runtime=diagnose(Path('.'),probe_act=True)
    if not runtime['act_ready']:
        parser.error('Current Linux filtered-worker gate failed')
    ledger=SpendLedger('controller_state/cloud-spend.sqlite')
    if ledger.summary()['accounted_upper_bound_usd']!=payload['accounted_start_usd']:
        parser.error('Spend changed since estimate; re-estimate before approval')
    args.output.mkdir(parents=True,exist_ok=False)
    claim_plan(Path('controller_state/steward-live-runs.sqlite'),digest,payload['test_manifest_sha256'])
    load_controller_environment(args.env_file)
    key=os.environ.get('NEBIUS_API_KEY','').strip()
    if not key:
        parser.error('Controller key missing; plan remains sealed')
    import httpx
    from openai import OpenAI
    with OpenAI(api_key=key,base_url=INFERENCE_BASE_URL,max_retries=0,timeout=60,
                http_client=httpx.Client(trust_env=False,follow_redirects=False)) as provider:
        client=RecordedClient(provider,args.output)
        summary=workload(payload,manifest,client,RunBudget(ledger,payload['stop_threshold_usd']),args.output)
        summary.update(provider_calls=len(client.records),plan_sha256=digest,ledger_end=ledger.summary())
        (args.output/'summary.json').write_bytes(canonical(summary))
        print(json.dumps(summary))


if __name__=='__main__':
    main()
