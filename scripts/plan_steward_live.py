"""Offline bounded WP6 plan; does not load credentials or create a client."""
import argparse
import hashlib
import json
import random
from pathlib import Path

from descend.controller.inference import NANO_MODEL_ID, SUPER_MODEL_ID, PRICE_POLICY
from descend.steward.corpus import canonical, verify_manifest


def plan(corpus=Path('eval/v1')):
    if PRICE_POLICY[SUPER_MODEL_ID][0]!=2 or PRICE_POLICY[NANO_MODEL_ID][0]!=1:
        raise ValueError('Conservative accounting policy changed; re-estimate explicitly')
    manifest = verify_manifest(corpus)
    tests = sorted(c['id'] for c in manifest['cases'] if c['split']=='test')
    repeats = sorted(random.Random(20261005).sample(tests,10))
    review_bound = 20000+8192+1000
    act_bound = 40000+8192+2000
    conservative = (52*review_bound*2 + 52*review_bound + 8*act_bound*2)/1000000
    files = ['descend/steward/reviewer.py','descend/steward/findings.py','descend/steward/act_proxy.py',
             'descend/steward/act.py','descend/steward/act_worker.py','descend/steward/act_seccomp.py',
             'requirements-lock.txt','requirements-steward-eval-lock.txt',
             'scripts/run_steward_live.py','scripts/plan_steward_live.py',
             'descend/controller/inference.py','descend/controller/token_factory.py',
             'descend/controller/environment.py','descend/controller/spend.py',
             'descend/steward/corpus.py','descend/steward/scoring.py',
             'descend/steward/doctor.py','descend/steward/watch.py','descend/steward/git_output.py']
    return dict(schema_version=1, status='PROPOSED_NOT_APPROVED_NOT_EXECUTED', provider_calls=0,
                test_manifest_sha256=(corpus/'test-manifest.sha256').read_text().strip(),
                models=[SUPER_MODEL_ID,NANO_MODEL_ID], primary_cases=tests, repeat_cases=repeats,
                repeat_seed=20261005, primary_calls=64, repeat_calls=40, act_call_cap=8,total_call_cap=112,
                reviewer_max_output_tokens=1000, act_max_output_tokens=2000, temperature=0,
                thinking=False,static_context=None, review_request_byte_cap=20000, act_request_byte_cap=40000,
                conservative_accounting_bound_usd=conservative, proposed_new_spend_cap_usd=8,
                expected_tokens={'review_prompt':500,'review_completion':300,'act_prompt':1200,'act_completion':800,
                                 'total':99200,'basis':'Planning assumptions informed by tiny historical pilots; not measured test-split usage'},
                expected_accounting_usd=0.1568,
                projected_remaining_ceiling_after_conservative_bound_usd=20-0.548195-conservative,
                stop_threshold_usd=6.4, cumulative_cap_usd=20, accounted_start_usd=0.548195,
                policy='Reserve each call before submission; stop before a reservation crosses $6.40 additional accounted spend. No automatic retries; retain ambiguous holds.',
                prerequisites=['Offline gates committed','Current Linux doctor and fresh-clone gates pass',
                               'Written approval of this quantified plan','Runner validates plan hashes and implements all caps'],
                limitation='Accounting bound uses in-tree conservative micro-dollar rates, not a current provider invoice or price quote. Billing receipt unavailable.',
                source_hashes={name:hashlib.sha256(Path(name).read_bytes()).hexdigest() for name in files})


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    payload=plan()
    args.output.parent.mkdir(parents=True,exist_ok=True)
    if args.output.exists():
        parser.error('Refusing to overwrite a frozen plan')
    args.output.write_bytes(canonical(payload))
    print(json.dumps({'provider_calls':0,'conservative_accounting_bound_usd':payload['conservative_accounting_bound_usd'],
                      'proposed_new_spend_cap_usd':8,'plan_sha256':hashlib.sha256(args.output.read_bytes()).hexdigest()}))


if __name__=='__main__':
    main()
