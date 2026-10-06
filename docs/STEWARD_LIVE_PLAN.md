# WP6 cost plan — approved 2026-10-06

The user explicitly approved this plan on 2026-10-06. The final frozen v4 SHA
is `f3e07c9831152bf60ecf8a4638a6f41bec02decbc85680fce5bec95fa07e47ce`.
Execution uses the $8 additional cap and $6.40 stop threshold. The JSON's
original proposed status is preserved as frozen input; controller approval is
stored separately. See [measured results](EVALUATION.md) for execution status.

Completed: 104 reviews and one act proposal, 105 calls total. The act proposal
failed syntax validation; seven candidates were not run after the halt. Additional
accounted spend $0.065495; cumulative $0.613690, no unresolved holds. The frozen
corpus claim remains sealed. Approval does not authorize a rerun or a new workload.

The proposed run has 64 primary reviews (32 frozen test cases each on Super and
Nano), 40 variance reviews (10 preselected cases repeated twice per model),
and at most 8 one-shot act proposals. Maximum **112 calls**. No fixture labels,
known fixes or generator reproducers may enter reviewer/proposal input.

Request caps: 20,000 bytes / 1000 output tokens for review; 40,000 bytes /
2000 output tokens for act. Temperature zero, thinking disabled, no Vibe/ASI
context. The offline planner freezes random case selection, corpus identity,
source hashes and dependency locks. Hash changes invalidate the plan.

Using the ledger's conservative accounting policy rather than list-price
estimates, the maximum reservations are **$5.357024**. Proposed new spend cap:
**$8**, with a stop before any reservation crosses **$6.40** (80%). The cumulative
$20 ceiling also remains enforced. Historical accounted spend is $0.548195;
there is no provider invoice reconciliation. Ambiguous failures retain their
reservation and have no automatic retry. This is not a current price quote.

Planning assumptions: 500 prompt + 300 completion tokens per review, and
1200 + 800 per act, approximately 99,200 tokens / $0.1568 conservative accounting.
These are assumptions informed by tiny earlier pilots, not measured test-split
usage. Maximum reservations, rather than these assumptions, govern the cap.
The projected remaining $20 ceiling after the maximum reservations is $14.094781.

The runner now implements an additional reservation limit over the durable
cumulative ledger, sealed plan claims, model-specific rates, raw request/response
records, primary/variance separation, error/miss preservation and bounded act
verification after all reviews. It keeps prompt text unchanged and changes only
the model selector for Nano. Protocol v1/v2/v3 plans are retained as superseded
preparation snapshots; final v4 pins the current runner and dependencies. Seeded
identities use diff hashes, not real-history Git commit SHAs. A corpus-level
claim blocks rerunning the same test split under a changed plan. Independent
red-team clearance remains pending and is not inferred from author-run checks.
`--check` validates the plan without reading the environment or constructing a
client. Launch required written approval naming the final quantified plan;
the user provided it before this run. The attached completion directive requires written
approval after the estimate; the general $20 credit statement does not replace
that specific gate. All live results, errors, usage IDs, hashes, false positives
and misses must be preserved and scored with the predeclared protocol.
