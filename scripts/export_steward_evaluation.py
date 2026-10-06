"""Read-only owned-corpus live report/export; never execute model text."""
import argparse
import hashlib
import html
import json
from pathlib import Path

from descend.steward.corpus import canonical, verify_manifest
from descend.steward.scoring import wilson
from descend.steward.watch import SECRET_LINE


def percent(metric):
    if metric['rate'] is None:
        return 'Undefined'
    low,high=metric['wilson95']
    return f"{metric['numerator']}/{metric['denominator']} ({metric['rate']*100:.1f}%; 95% {low*100:.1f}–{high*100:.1f}%)"


def export(source, output):
    manifest=verify_manifest(Path('eval/v1'))
    summary=json.loads((source/'summary.json').read_text())
    if summary['kind']!='live' or summary['plan_sha256']!='f3e07c9831152bf60ecf8a4638a6f41bec02decbc85680fce5bec95fa07e47ce':
        raise ValueError('Expected approved frozen owned-corpus run')
    arms={arm:json.loads((source/(arm+'-scores.json')).read_text()) for arm in ('Super','Nano')}
    primary={arm:json.loads((source/(arm+'.json')).read_text())['results'] for arm in arms}
    variance=json.loads((source/'variance.json').read_text())
    owned={case['id'] for case in manifest['cases'] if case['split']=='test'}
    for arm,rows in primary.items():
        ids=[row['case'] for row in rows]
        if len(ids)!=32 or set(ids)!=owned:
            raise ValueError('Only complete owned frozen primary results may be exported')
        score=arms[arm]
        cited=set(score['misses'])|{r['case'] for key in ('false_positives','errors','classifications') for r in score[key]}
        if not cited<=owned:
            raise ValueError('Unowned result identity refused')
    if len(variance)!=40 or any(row['case'] not in owned for row in variance):
        raise ValueError('Owned repeat results required')
    act=json.loads((source/'act-metrics.json').read_text())
    consistency={}
    for arm in arms:
        model=primary[arm][0]['model']
        ids=sorted({r['case'] for r in variance if r['model']==model})
        groups=[]
        for identifier in ids:
            rows=[r for r in primary[arm]+variance if r['model']==model and r['case']==identifier]
            signatures=[sorted((f['path'],f['line'],f['evidence'].strip()) for f in row.get('findings',[])) for row in rows]
            # Invalid output is a distinct outcome, never silently equivalent to abstention.
            flags=[(row.get('error'),row.get('parse_error')) for row in rows]
            groups.append({'case':identifier,'runs':len(rows),'stable_citations_and_parse_status':all(s==signatures[0] for s in signatures) and all(f==flags[0] for f in flags)})
        consistency[arm]={'definition':'Same accepted citation set and parse/error status across primary plus two repeats; reason wording excluded',
                          'stable':wilson(sum(g['stable_citations_and_parse_status'] for g in groups),len(groups)),'cases':groups}
    lines=['# Repo Steward live evaluation — 2026-10-06','',
           'LIVE Token Factory responses on the owned frozen seeded test split. Automatic citation/location scores; human adjudication remains pending.',
           '', '| Arm | Recall, Wilson 95% | Precision, Wilson 95% | Clean alarms, Wilson 95% | Decoy alarms | Median review latency | Accounted primary cost |',
           '|---|---|---|---|---|---|---|']
    for arm in ('B0','B1','Super','Nano'):
        score=arms[arm] if arm in arms else json.loads((Path('docs/evidence/steward-baselines-v1')/(arm+'-test')/'scores.json').read_text())
        latency=score['latency_seconds']['median']
        lines.append(f"| {arm} | {percent(score['recall'])} | {percent(score['precision'])} | {percent(score['clean_false_alarm'])} | {percent(score['decoy_false_alarm'])} | {latency:.3f}s | ${score['cost_usd']['total'] or 0:.6f} |" if latency is not None else
                     f"| {arm} | {percent(score['recall'])} | {percent(score['precision'])} | {percent(score['clean_false_alarm'])} | {percent(score['decoy_false_alarm'])} | Not observed | $0 |")
    lines+=['','Super has 16 location-matched findings across 15 detected bug cases; recall counts cases, precision counts deduplicated findings. Seven primary Super outputs violated the response schema; its low control alarm rate includes these failures, so it is not proof of reliable abstention.',
            '',f"Run: {summary['provider_calls']} calls, 104 reviews including repeats, {summary['act_attempts']} act attempt. Additional accounted upper bound ${summary['additional_accounted_upper_bound_usd']:.6f}; cumulative ${summary['ledger_end']['accounted_upper_bound_usd']:.6f} / $20, unresolved holds {summary['ledger_end']['unresolved_calls']}. No billing receipt. All calls and failures retained; no retries or rerun.",
            '', '## Act result','',f"Patch verification: {percent(act['verification'])}. The first proposal was rejected before execution for invalid Python syntax: literal backslash-n sequences remained inside the JSON source strings. It also used unsupported imports/test naming. The run halted acts fail-closed; seven remaining candidates are NOT_RUN. No live patch was verified or applied.",
            '', '## Repeat consistency','']
    for arm,data in consistency.items():
        lines.append(f"- {arm}: {percent(data['stable'])} stable selected cases across three observations. Raw repeats retained; this is a small correlated sample.")
    lines+=['','## Every false positive','']
    for arm,score in arms.items():
        for row in score['false_positives']:
            finding=row['finding']
            explanation='Non-executing injection text was treated as a bug.' if row['case'].startswith('decoy-') else 'Behavior-preserving code/comment was reported as a bug or style concern.'
            lines.append(f"- **{arm} / {row['case']} / {finding['path']}:{finding['line']}**: {explanation} Model reason: {finding['reason']}")
    lines+=['','## Every miss','']
    for arm,score in arms.items():
        for identifier in score['misses']:
            lines.append(f'- **{arm} / {identifier}**: no accepted finding within the predeclared location tolerance of the seeded bug.')
    lines.append('- **B0 and B1** each missed all 16 test bugs; the complete IDs and weak-baseline explanation remain in EVALUATION.md and their score files.')
    lines+=['','## Every response error','']
    for arm,score in arms.items():
        for error in score['errors']:
            lines.append(f"- **{arm} / {error['case']}**: {error['error']}. Raw content retained.")
    lines+=['','Six Super primary responses contained pseudo runtime/API timeout messages as model content; one returned a bare array rather than the required findings object. These were successful SDK responses with usage, not observed controller transport timeouts. Their origin is unproven; the controller did not retry.',
            '', '## What this does not show','',
            'No general repository accuracy, production safety, independent red-team clearance, semantic human adjudication, successful model-generated patch, fine-tuning, deployment or model improvement is established. Location matching ±2 is weak on tiny functions; families repeat across splits and Wilson intervals assume independence that this corpus does not provide. Provider weight/version identity is unavailable. The baseline smoke tests are weak. Costs are conservative local accounting, not invoices. The public demo remains a separately labeled mock.', '']
    report='\n'.join(lines)
    public={'kind':'LIVE / owned seeded fixture evaluation','summary':summary,'scores':arms,'repeat_consistency':consistency,'act_metrics':act,
            'limitation':'Automatic location scoring; human adjudication and independent red-team pending; live patch rejected, no checkout application'}
    page='<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Repo Steward live results</title><style>body{max-width:1000px;margin:40px auto;padding:20px;font:17px system-ui;background:#101923;color:#e7edf5}pre{white-space:pre-wrap;overflow-wrap:anywhere}h1{color:#8ddcc9}</style><h1>Repo Steward: live results</h1><p>Owned seeded fixtures. Automatic scores. No patch applied. Independent review pending.</p><pre>'+html.escape(report)+'</pre></html>'
    payloads={'REPORT.md':report.encode(),'repeat-consistency.json':canonical(consistency),
              'public/data.json':canonical(public),'public/index.html':page.encode(),'public/LICENSE':Path('LICENSE').read_bytes()}
    for data in payloads.values():
        if SECRET_LINE.search(data.decode('utf-8')):
            raise ValueError('Sensitive-content pattern in public export')
    files={name.split('/')[-1]:hashlib.sha256(data).hexdigest() for name,data in payloads.items() if name.startswith('public/')}
    payloads['public/manifest.json']=canonical({'files':files,'license':'Descend LICENSE; original owned fixtures','source_plan_sha256':summary['plan_sha256'],'secret_pattern_matches':0})
    size=sum(len(data) for name,data in payloads.items() if name.startswith('public/'))
    if size>500000:
        raise ValueError('Public bundle cap exceeded')
    output.mkdir(parents=True,exist_ok=False)
    for name,data in payloads.items():
        path=output/name
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)
    print(json.dumps({'public_bytes':size,'secret_pattern_matches':0,'report':str(output/'REPORT.md')}))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    export(args.source,args.output)


if __name__=='__main__':
    main()
