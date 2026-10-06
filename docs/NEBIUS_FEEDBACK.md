# Nebius / NVIDIA integration feedback

## Frozen live evaluation, 2026-10-06

105 successful SDK responses carried 32,322 prompt and 11,641 completion tokens.
The primary review medians were 1.051 seconds (Super) and 0.931 seconds (Nano),
including controller validation/accounting. Additional conservative accounting:
$0.065495; cumulative $0.613690. This is not an invoice.

Seven primary Super outputs violated the required findings-object schema. Six
contained text claiming agent/API 90-second timeouts and retries, despite being
successful short SDK responses; one returned a bare array. Their origin is
unknown, and controller retries were disabled. A provider explanation or reliable
structured-output contract would help. Raw IDs/usage and text are retained in
[the live evidence](evidence/steward-live-20261006/ARTIFACT_MANIFEST.json).

The first Super act proposal double-escaped newline sequences, producing invalid
Python after JSON decoding. It also departed from the required import/test
convention. The controller rejected it before execution and stopped acts without
retry. Nano often returned a finding whose reason explicitly said the change was
not a bug. These failures show why citation checking alone is insufficient.
See [complete results and limitations](STEWARD_LIVE_RESULTS.md).

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
Fine-tuning and LoRA deployment remain unmeasured. The seeded reviewer
measurement above is separate from those earlier offline checks.
