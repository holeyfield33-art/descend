# Repo Steward evaluation

Status: offline seeded baselines only, 2026-10-05. No Super/Nano corpus run,
act verification or human adjudication has occurred. Metrics were declared in
[STEWARD_METRICS.md](STEWARD_METRICS.md) before any model run.

Frozen corpus commit `a810a3f`; 44 total cases, 12 dev and 32 test. Test contains
16 bugs, 11 clean/hard negatives and 5 injection decoys. The separate label
check passed all 68 expected outcomes; those checks use ground truth and are
not baseline or model findings.

| Arm, frozen test split | Recall (Wilson 95%) | Precision | Clean false-alarm (Wilson 95%) | Cost |
|---|---|---|---|---|
| B0 no-op | 0/16, 0% [0%, 19.36%] | Undefined, no findings | 0/11, 0% [0%, 25.88%] | $0 |
| B1 existing tests + ruff | 0/16, 0% [0%, 19.36%] | Undefined, no findings | 0/11, 0% [0%, 25.88%] | $0 |
| Nemotron Super | Not run | Not run | Not run | No new spend |
| Nemotron Nano | Not run | Not run | Not run | No new spend |

Both offline arms have zero findings, zero false positives and 16 misses on
test. Decoy false-alarm is 0/5 [0%, 43.45%]. Citation-valid rate is undefined
with no findings. B1 median processing latency was 2.417 seconds, including
both base and review sandbox executions; this is not provider inference latency.
There were no baseline tool errors across all 44 cases. No measured act
verification rate exists. Blind sheets are empty because neither baseline
emitted findings; adjudicated metrics remain null.

## Every missed test bug (both baselines)

- `bug-off_by_one-1`
- `bug-empty_check-1`
- `bug-wrong_default-1`
- `bug-swapped_arguments-1`
- `bug-resource_close-1`
- `bug-stale_state-1`
- `bug-encoding-1`
- `bug-exception-1`
- `bug-shared_mutation-1`
- `bug-off_by_one-2`
- `bug-comparison-2`
- `bug-swapped_arguments-2`
- `bug-boundary-2`
- `bug-encoding-2`
- `bug-exception-2`
- `bug-shared_mutation-2`

B0 is defined to report nothing. B1 misses these behavioral defects because
the existing tests only check that the API is callable, and ruff emits no new
diagnostic on the changed lines. This corpus supplies a particularly weak B1;
beating it would not establish superiority to realistic test suites or review.
There are no false positives to explain for these arms. Full outputs, all cases
and scores are in [`evidence/steward-baselines-v1/`](evidence/steward-baselines-v1/).

## What this does not show

No model review accuracy, production-repository performance, security guarantee,
successful generated patch or generalization to unseen bug families. Cases are
tiny, synthetic and correlated across splits; Wilson intervals do not account
for that correlation. The six source-level decoys are not the complete WP4
injection matrix. Model parameters/source are frozen separately, but provider
sampling, model drift and latency will remain non-reproducible elements.
