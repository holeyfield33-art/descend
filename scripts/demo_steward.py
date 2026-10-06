"""One-command Linux offline demo on an owned Git fixture; no provider client."""
import argparse
import hashlib
import html
import json
import os
import subprocess
import tempfile
from pathlib import Path

from descend.steward.act import ActStore, verify_proposal
from descend.steward.corpus import canonical
from descend.steward.findings import added_lines, validate_findings
from descend.steward.watch import GIT_EXECUTABLE, SECRET_LINE, ReviewStore, git_environment, scan_once
from scripts.run_steward_act import materialize_git

GOOD = 'def solve(values):\n    return sum(values)\n'
BAD = 'def solve(values):\n    return sum(values[:-1])\n'
TEST = 'from app import solve\ndef test_existing():\n    assert callable(solve)\n'
REPRO = 'from app import solve\ndef test_reproducer():\n    assert solve([1, 2]) == 3\n'


def run(output: Path) -> dict:
    output.mkdir(parents=True, exist_ok=False)
    with tempfile.TemporaryDirectory(prefix='steward-demo-') as temporary:
        repo = Path(temporary) / 'owned-fixture'
        repo.mkdir()
        def git(*args):
            return subprocess.run([GIT_EXECUTABLE, '-c', 'core.hooksPath='+os.devnull,
                                   '-c', 'user.name=Owned demo', '-c', 'user.email=demo@example.invalid',
                                   '-C', str(repo), *args], env=git_environment(), check=True,
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE).stdout
        git('init')
        (repo/'app.py').write_text(GOOD, encoding='utf-8', newline='\n')
        (repo/'tests').mkdir()
        (repo/'tests/test_existing.py').write_text(TEST, encoding='utf-8', newline='\n')
        git('add', '.')
        git('commit', '-m', 'Owned clean fixture')
        calls = []
        def mock(snapshot):
            calls.append(snapshot['sha'])
            findings = []
            for (path, line), evidence in added_lines(snapshot['diff']).items():
                if evidence.strip() == 'return sum(values[:-1])':
                    findings.append(dict(path=path, line=line, evidence=evidence, severity='medium',
                                         reason='MOCK: final item omitted', verification='Assert sum of [1, 2] is 3'))
            raw = json.dumps({'findings': findings})
            return dict(protocol_version=2, content=raw, **validate_findings(raw, snapshot['diff'], snapshot['paths']))
        database = output/'reviews.sqlite'
        store = ReviewStore(database)
        scan_once(repo, store, mock)
        before_idle = len(calls)
        idle = scan_once(repo, store, mock)
        idle_calls = len(calls) - before_idle
        (repo/'app.py').write_text(BAD, encoding='utf-8', newline='\n')
        git('add', '.')
        git('commit', '-m', 'Owned seeded bug')
        review = scan_once(repo, store, mock)
        sha = review['sha']
        actions = ActStore(output/'acts.sqlite')
        assert actions.claim('owned-demo', sha, 0, commit_cap=1)
        snapshot = Path(temporary)/'snapshot'
        snapshot.mkdir()
        diff = materialize_git(repo, sha, snapshot)
        proposal = json.dumps(dict(path='app.py', test_source=REPRO, replacement_source=GOOD, expected_failure='AssertionError'))
        result = verify_proposal(snapshot, review['review']['findings'][0], proposal, output/'exports',
                                 review_diff=diff, identity={'repo': 'owned-demo', 'reviewed_commit': sha, 'finding_index': 0})
        actions.finish('owned-demo', sha, 0, result)
        before_restart = len(calls)
        restarted = scan_once(repo, ReviewStore(database), mock)
        repeat_action = ActStore(output/'acts.sqlite').claim('owned-demo', sha, 0, commit_cap=1)
        report = dict(schema_version=1, kind='mock/owned seeded fixture', provider_calls=0, cost_usd=0,
                      reviewed_commit=sha, idle_cached=idle['cached'], idle_mock_calls=idle_calls,
                      new_bug_findings=len(review['review']['findings']), mock_review_calls=len(calls),
                      classification=result['classification'], restart_cached=restarted['cached'],
                      restart_mock_calls=len(calls)-before_restart, repeated_action_claim=repeat_action,
                      checkout_unchanged=(repo/'app.py').read_text()==BAD and git('status','--porcelain')==b'',
                      source_root_unchanged=result['source_root_unchanged'], patch_export=result['patch_export'],
                      human_approval='Required before manually applying an exported patch; no apply tool exists',
                      limitation='Canned finding and known test/fix; this measures controller behavior, not Nemotron quality')
        report['complete'] = (idle['cached'] and idle_calls==0 and len(calls)==2 and before_restart==2 and restarted['cached']
                              and not repeat_action and result['classification']=='PATCH_VERIFIED'
                              and report['checkout_unchanged'] and report['source_root_unchanged'])
        (output/'report.json').write_bytes(canonical(report))
        baseline = {}
        for arm in ('B0', 'B1'):
            score = json.loads((Path('docs/evidence/steward-baselines-v1')/(arm+'-test')/'scores.json').read_text())
            baseline[arm] = {key: score[key] for key in ('cases', 'precision', 'recall', 'clean_false_alarm', 'citation_valid')}
        public = {'demo': report, 'owned_fixture': {'review': BAD, 'fix': GOOD, 'test': REPRO},
                  'evaluation': {'baseline_test_metrics': baseline,
                                 'baseline_limitation': 'Existing tests only check callable API; all 16 seeded test bugs missed. No model accuracy measured.',
                                 'live_model_measurement': 'Not run', 'independent_redteam': 'Pending'}}
        bundle = output/'public'
        bundle.mkdir()
        data = canonical(public)
        if SECRET_LINE.search(data.decode()):
            raise ValueError('Public bundle sensitive-content scan rejected')
        (bundle/'data.json').write_bytes(data)
        page = '<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>Repo Steward offline evidence</title><style>body{max-width:900px;margin:40px auto;padding:20px;font:17px system-ui;background:#101923;color:#e7edf5}pre{white-space:pre-wrap;overflow-wrap:anywhere}h1{color:#8ddcc9}</style><h1>Repo Steward: offline evidence</h1><p>MOCK / owned seeded fixture. No provider calls. Export only. Live model results and independent red-team review are pending.</p><pre>'+html.escape(json.dumps(public,indent=2))+'</pre></html>'
        (bundle/'index.html').write_text(page,encoding='utf-8')
        license_bytes = Path('LICENSE').read_bytes()
        (bundle/'LICENSE').write_bytes(license_bytes)
        files = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in bundle.iterdir()}
        (bundle/'manifest.json').write_bytes(canonical({'origin':'Original Descend owned fixture; no sibling data', 'license':'See LICENSE', 'files':files, 'secret_pattern_matches':0}))
        if sum(p.stat().st_size for p in bundle.iterdir()) > 500000:
            raise ValueError('Public bundle size cap exceeded')
        return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True, help='New output directory; refuses overwrite')
    args = parser.parse_args()
    if os.name != 'posix':
        parser.error('Run in provisioned Linux/WSL; native Windows cannot execute this worker')
    report = run(args.output)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['complete'] else 1)


if __name__ == '__main__':
    main()
