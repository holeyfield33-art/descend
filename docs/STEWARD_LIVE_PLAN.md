# Proposed WP6 cost plan — not approved or executed

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

The runner still needs its offline contract checks and current Linux/fresh-clone
gate. No live invocation is offered until those pass and written approval names
this quantified plan. The user's attached completion directive requires written
approval after the estimate; the general $20 credit statement does not replace
that specific gate. All live results, errors, usage IDs, hashes, false positives
and misses must be preserved and scored with the predeclared protocol.
