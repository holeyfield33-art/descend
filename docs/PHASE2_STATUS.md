# Phase 2 status

## Scope and authorization

The user authorized autonomous DM0 work with a total cloud-spend ceiling of **$20**. Phase 2A uses real Nemotron inference with fake training and synthetic scoring. Its output is **PILOT — NOT CLAIM-BEARING**. No formal preregistration is frozen and no formal seed has run.

## Authenticated discovery

Read-only `GET /v1/models` succeeded and listed 25 models, including `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Dedicated endpoint templates were retrieved. A probe of `/v1/fine_tuning/models` returned 404; it is not a catalog route in the retrieved OpenAPI specification. Spec-draft training has a separate catalog and is not interchangeable with DM0 LoRA training.

The [official Nemotron page](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference) lists Nano at $0.06 per million input tokens and $0.24 per million output tokens. Inference reserves and settles at a conservative $1 per million for both. SQLite transactions enforce a cumulative $20 limit across process restarts and concurrent reservations. Unknown outcomes retain the full hold; retries are disabled. This accounting is an upper-bound estimate under the verified price schedule, not a billing receipt or account-credit query. Provider-side price changes and activity outside Descend are outside this ledger.

## Local gates and implementation

- The same evidence reference now determines A and B. Nemotron input-content lengths are matched with pinned tokenizer data from NVIDIA; no remote model code is executed.
- The runtime dependency lock contains exact versions for all installed dependencies, including provider tooling.
- Registry head/count anchors detect valid-prefix and total truncation. Anchors are controller-owned; they do not protect against a compromised trusted controller rewriting both files. Legacy logs without anchors are explicitly unverified, never silently migrated.
- Fake adapter bytes, dataset/config bytes, and actual controller/evaluator/promotion source hashes are bound and rechecked. The synthetic base identity remains explicitly a fake model specification.
- Provider usage is recorded separately and charged to the conservative run token counter. Credentials remain controller-only. Each model tool proposal passes through the existing Linux isolated JSON relay and run-scoped dispatcher.
- The four-attempt viability plan uses seeds 201–204, alternating A/B, identical sampling configuration and budgets. All attempts, failures, provider IDs, transcripts, commitments, registry verification and accounting are preserved. GO requires at least 3/4 autonomous protocol completions.

## Remaining experimental gates

Real fine-tuning requires a supported small target with a verified deployment path and bounded cost. The [fine-tuning model guide](https://docs.tokenfactory.nebius.com/post-training/models) lists Qwen2.5-0.5B-Instruct, Qwen3-0.6B and Llama-3.2-1B-Instruct, but states that deployment currently uses dedicated endpoints. The authenticated templates do not establish an end-to-end deployment path for those small targets. Do not substitute a much larger target or submit an unbounded job to work around this gap.

Before claim runs: validate real training/deployment/evaluation, obtain real pilot cost and task-difficulty evidence, freeze the Arm C recipe and prediction baselines, commit preregistration with 12 paired seeds and `delta_min`, verify provider input-length behavior, then freeze code. H1 cannot be evaluated using Phase 2A synthetic scores.
