"""Offline provider-contract and fail-closed run controls; fake ledger/client."""
import json
import sys
from types import SimpleNamespace

import pytest

from descend.controller.spend import SpendLedger, SpendExhausted
from descend.steward.corpus import verify_manifest
from descend.sandbox.hard_isolation import isolation_available
from scripts.plan_steward_live import plan
from scripts.run_steward_live import RecordedClient, RunBudget, claim_plan, workload
from pathlib import Path


def test_additional_budget_holds_ambiguous_calls_and_seals_run(tmp_path):
    ledger = SpendLedger(tmp_path/'mock.sqlite')
    budget = RunBudget(ledger,.001)
    first = budget.reserve('mock',900)
    with pytest.raises(SpendExhausted):
        budget.reserve('mock',101)
    assert ledger.summary()['calls']==1
    budget.settle(first,100,'mock')
    budget.reserve('mock',900)
    with pytest.raises(SpendExhausted):
        budget.reserve('mock',1)
    claim_plan(tmp_path/'runs.sqlite','mock-plan')
    with pytest.raises(RuntimeError):
        claim_plan(tmp_path/'runs.sqlite','mock-plan')
    claim_plan(tmp_path/'runs.sqlite','first-plan','frozen-corpus')
    with pytest.raises(RuntimeError):
        claim_plan(tmp_path/'runs.sqlite','changed-plan','frozen-corpus')


def test_full_frozen_workload_with_fake_provider_has_no_oracle_input(tmp_path):
    payload=plan()
    calls=[]
    def create(**body):
        calls.append(body)
        user=body['messages'][1]['content']
        assert 'test_reproducer' not in user and 'replacement_source' not in user
        assert len(json.dumps({k:v for k,v in body.items() if k!='timeout'},ensure_ascii=False).encode())<=20000
        return SimpleNamespace(model_dump=lambda **_: {'id':'mock-'+str(len(calls)),
                               'usage':{'prompt_tokens':10,'completion_tokens':5},
                               'choices':[{'message':{'content':'{"findings": []}'}}]})
    fake=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    client=RecordedClient(fake,tmp_path)
    budget=RunBudget(SpendLedger(tmp_path/'mock.sqlite'),6.4)
    result=workload(payload,verify_manifest(Path('eval/v1')),client,budget,tmp_path)
    assert len(calls)==104 and result['act_attempts']==0 and not result['halted']
    assert sum(c['model']==payload['models'][0] for c in calls)==52
    assert sum(c['model']==payload['models'][1] for c in calls)==52
    for arm in ('Super','Nano'):
        scores=json.loads((tmp_path/(arm+'-scores.json')).read_text())
        assert scores['cases']==32 and len(scores['misses'])==16
    assert len(list(tmp_path.glob('call-*.response.json')))==104


@pytest.mark.skipif(sys.platform!='linux' or not isolation_available()['available'],reason='Live-act contract probe requires Linux worker; provider remains fake')
def test_canned_proposal_runs_after_all_reviews_and_gets_live_origin_card(tmp_path):
    payload=plan()
    calls=[]
    def create(**body):
        calls.append(body)
        if body['max_tokens']==2000:
            content=json.dumps(dict(path='app.py',test_source='from app import solve\ndef test_reproducer():\n    assert solve([1, 2]) == 3\n',
                                    replacement_source='def solve(values):\n    return sum(values)\n',expected_failure='AssertionError'))
        else:
            findings=[]
            diff=body['messages'][1]['content'].split('<untrusted_diff>\n',1)[1].split('\n</untrusted_diff>',1)[0]
            from descend.steward.findings import added_lines
            for (path,line),evidence in added_lines(diff).items():
                if evidence.strip()=='return sum(values[:-1])':
                    findings.append(dict(path=path,line=line,evidence=evidence,severity='medium',reason='MOCK omission',verification='Assert sum'))
            content=json.dumps({'findings':findings})
        return SimpleNamespace(model_dump=lambda **_: {'id':'mock-live-contract', 'usage':{'prompt_tokens':20,'completion_tokens':20},
                               'choices':[{'message':{'content':content}}]})
    fake=SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    fake.with_options=lambda **_:fake
    result=workload(payload,verify_manifest(Path('eval/v1')),RecordedClient(fake,tmp_path),
                    RunBudget(SpendLedger(tmp_path/'mock.sqlite'),6.4),tmp_path)
    assert not result['halted'] and result['act_attempts']>0
    assert all(c['max_tokens']==1000 for c in calls[:104])
    acts=json.loads((tmp_path/'acts.json').read_text())
    assert all(r['verification']['classification']=='PATCH_VERIFIED' for r in acts)
    assert all(r['verification']['kind']=='live' and r['verification']['source_root_unchanged'] for r in acts)


def test_approval_mismatch_stops_before_runtime_or_credentials(tmp_path,monkeypatch):
    from descend.steward.corpus import canonical
    from scripts import run_steward_live as runner
    frozen=tmp_path/'plan.json'
    frozen.write_bytes(canonical(plan()))
    approval=tmp_path/'approval.txt'
    approval.write_text('APPROVE PLAN wrong-hash CAP_USD 8')
    def forbidden(*args,**kwargs):
        raise AssertionError('Approval must precede runtime/key access')
    monkeypatch.setattr(runner,'diagnose',forbidden)
    monkeypatch.setattr(runner,'load_controller_environment',forbidden)
    monkeypatch.setattr(sys,'argv',['runner','--plan',str(frozen),'--approval',str(approval),
                                    '--output',str(tmp_path/'output')])
    with pytest.raises(SystemExit) as rejected:
        runner.main()
    assert rejected.value.code==2 and not (tmp_path/'output').exists()
