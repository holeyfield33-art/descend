# Nebius / NVIDIA integration feedback

Descend uses the official Token Factory cookbook as a read-only codebook.
The smallest chat-completion pattern is adapted into controller-side request
helpers and the Steward review/act proxies. No upstream dependency is required
at runtime. [Reference notes](TOKEN_FACTORY_REFERENCE.md) record the inspected
commit, MIT attribution and current API discrepancies.

Historical Super inference pilots returned structured findings with measured
usage (266 prompt / 383 completion tokens and 345 / 157). One reported line
needed unique exact-added-line correction. The optional Vibe/ASI context pilot
used 2991 / 163 tokens and produced a dismissed false positive. These tiny,
selected feasibility pilots demonstrate connectivity and citation plumbing;
they do not establish comparative accuracy. See
[pilot/context evidence](VIBE_EXPLAINER_REVIEW.md) and
[Steward project notes](HACKATHON_REPO_STEWARD.md).

Useful improvements: document `chat_template_kwargs.enable_thinking` for these
model IDs; expose stable model/deployment version identities for repeatable
evaluations; provide examples for strict structured finding responses and
usage/error handling with retries disabled; clarify the legacy notebook model
creation flow versus current LoRA/deployment API; keep fine-tuning learning-rate
field names and terminal states synchronized across notebooks and docs.

The controller preserves ambiguous spend reservations and provider IDs rather
than automatically retrying. Accounted spend is an upper bound, not a provider
invoice. No new provider run was made for the offline security/demo phase.
Fine-tuning, LoRA deployment and model-quality evaluation remain unmeasured.
