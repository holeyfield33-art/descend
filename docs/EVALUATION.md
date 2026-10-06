# Repo Steward evaluation

Status: live evaluation completed on 2026-10-06. See the
[full live report](STEWARD_LIVE_RESULTS.md) for Wilson intervals, every false
positive/miss/error, repeat consistency and preserved raw responses.

| Live primary arm, 32 cases | Automatic recall | Automatic precision | Clean/hard-negative alarms | Response schema errors |
|---|---|---|---|---|
| Super | 15/16 | 16/17 | 0/11 | 7 |
| Nano | 15/16 | 15/29 | 11/11 | 0 |

The Super alarm denominator includes invalid responses; it does not establish
reliable abstention. Both arms had 9/10 selected cases with stable citations and
parse status across the primary and two repeat reviews. One live act proposal
was rejected for invalid Python syntax before execution; seven candidates were
not run after the fail-closed halt. Live patch verification is 0/1 attempted
proposals, not a broad model success estimate. No live patch was applied.
105 provider calls added $0.065495 accounted upper bound; cumulative $0.613690,
223 calls, zero unresolved holds. There is no provider billing receipt.

Offline act verification passed 24 known fixture test/fix
pairs; that mock/oracle result is not model patch quality. Human adjudication
remains pending. Metrics were declared in
[STEWARD_METRICS.md](STEWARD_METRICS.md) before any model run.

Frozen corpus commit `a810a3f`; 44 total cases, 12 dev and 32 test. Test contains
16 bugs, 11 clean/hard negatives and 5 injection decoys. The separate label
check passed all 68 expected outcomes; those checks use ground truth and are
not baseline or model findings.

| Arm, frozen test split | Recall (Wilson 95%) | Precision | Clean false-alarm (Wilson 95%) | Cost |
|---|---|---|---|---|
| B0 no-op | 0/16, 0% [0%, 19.36%] | Undefined, no findings | 0/11, 0% [0%, 25.88%] | $0 |
| B1 existing tests + ruff | 0/16, 0% [0%, 19.36%] | Undefined, no findings | 0/11, 0% [0%, 25.88%] | $0 |
| Nemotron Super | 15/16, 93.8% [71.7%, 98.9%] | 16/17, 94.1% [73.0%, 99.0%] | 0/11, 0% [0%, 25.88%], includes schema failures | $0.025370 primary |
| Nemotron Nano | 15/16, 93.8% [71.7%, 98.9%] | 15/29, 51.7% [34.4%, 68.6%] | 11/11, 100% [74.1%, 100%] | $0.013747 primary |

Both offline arms have zero findings, zero false positives and 16 misses on
test. Decoy false-alarm is 0/5 [0%, 43.45%]. Citation-valid rate is undefined
with no findings. B1 median processing latency was 2.417 seconds, including
both base and review sandbox executions; this is not provider inference latency.
There were no baseline tool errors across all 44 cases. Neither baseline
attempted act verification. Their blind sheets are empty because neither baseline
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
