# Phase 2 status

## Current result

**Phase 2A GO:** Nemotron Super completed **4/4** autonomous protocols at seeds 217–220, implementation `b08b25b8b9bfe06d4b1a882de783d92fbd7e98ec`. Evidence is preserved at `artifacts/pilots/viability/20261004T164727Z-96bc6d4a`. Every registry and frozen-artifact audit passed. Live budget schemas resolved the previous budget-overrun pattern without changing the caps. Ultra was not needed.

Across all five batches: **20 attempts, 113 inference calls**, estimated list-price cost **$0.07699146**, conservative ledger total **$0.533707**, no unresolved calls. These are accounting estimates, not a billing receipt. All failed batches remain included. Four later batches preserve exact runtime source bytes; the first failed batch has source hashes/Git identity but no byte-for-byte snapshot.

Input-content lengths matched using pinned tokenizer data. In the successful Super batch, initial provider prompt usage was **1467 tokens for A and 1468 for B**. That private-wrapper difference remains unresolved before formal experiments; the viability GO concerns protocol completion only.

Following the user's request to make the best choice, the proposed pre-formal matching policy is **exact local content-token equality and at most one provider prompt token difference**. This makes the intended approximate matching concrete. The observed difference is within that proposed tolerance; exact provider equality has not been established. Freeze this policy in the eventual preregistration and verify each pair's initial counts. Larger differences must not be silently accepted or excluded after observing outcomes.

**Phase 2B external gate:** no real training job or paid deployment has been submitted. Account-specific training price and a verified small-target deployment/custom-weight path are needed to bound this phase within $20. The API and available read-only documentation did not establish that path. Browser tools could not access the pricing console. No claim-bearing data, frozen preregistration or formal result exists.

Reproduce the archive checks without cloud calls: `python -m scripts.audit_viability`.

## Continued real-weight work

The user requested the best choice and continued progress. A separate local CPU real-LoRA feasibility pilot completed successfully with Qwen2.5-0.5B-Instruct, including saved-adapter reload, at zero additional cloud spend. Accuracy remained 0/4. Five subsequent base-calibration recipes remained below the 25–60% range; the next tested candidate is Qwen3-0.6B. This is an explicitly disclosed local backend, not a completed Token Factory training/deployment route. [Local pilot notes](LOCAL_REAL_WEIGHT_PILOT.md) contain hashes, results and the task-definition correction.

Two bounded provider-length calibration calls preserve the JSON-neutral revision at `artifacts/pilots/length-calibration/20261004T171504Z`. Input-content lengths matched, but provider prompt counts were 1468/1469. The difference remains measured, not claimed resolved. Cumulative conservative inference accounting is now **$0.539585 across 115 calls**, no unresolved holds. Hidden and formal datasets remain untouched in local feasibility/calibration work.

Read-only account checks on 2026-10-04 returned HTTP 200 for `/v1/fine_tuning/jobs` and `/v0/dedicated_endpoints`, both with zero existing objects. The credential can access those listing routes; this does not verify submission rights, small-target deployment or pricing. No cloud training job or deployment was created.

Qwen3-0.6B scored 0/10 on each of three tested recipes both without and with input-character constrained decoding. The failed runs are preserved under `artifacts/pilots/local-calibration/`. Neither small target has met the 25–60% base-difficulty gate, and no formal target is selected. The local backend remains separate from the unverified Token Factory training/deployment path.

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

The first real Nano viability batch (seeds 201–204, code `1973cec71ed212e0fd15079410dc54ad3754b895`) completed **0/4** protocols. Three attempts breached the cumulative data-generation limit; one consumed its 4096-token output cap during reasoning and returned no tool call. All failed attempts and valid registry chains are preserved under `artifacts/pilots/viability/20261004T081110Z-249a2674`. Its 13 provider calls cost an estimated $0.0059601 at the listed rates; conservative ledger accounting was $0.042095.

Before escalating the model, the integration was corrected to provide live operational counters after tools and explicit cumulative generator limits. Neutral control text now uses ordinary prose instead of a repeated word. NVIDIA's [documented reasoning-off request pattern](https://huggingface.co/nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16) sets `chat_template_kwargs.enable_thinking=false`; this is logged identically for both arms and must be validated against the provider. A new batch uses viability-only seeds 205–208. The failed batch is not deleted or relabeled as a success.

The corrected batch at code `92227a20f54f50c1aa699f80c324c07f8ae397fa` completed **2/4**: A seeds 205/207 completed; B seeds 206/208 returned an action as plain JSON text and never invoked a tool. The initial provider prompt count was **1577 tokens in all four runs**, and tokenizer input-content counts matched at 526. Reasoning-off behavior was observed. Evidence is preserved under `artifacts/pilots/viability/20261004T163505Z-fe2f0233`, including the actual runtime source snapshot. This is a protocol result on a fake backend, not evidence for H1.

The next bounded implementation correction sets standard `tool_choice=required` while the protocol is open, then `none` after both commitments. This ensures a model action uses the offered function transport rather than an ad hoc JSON interpreter. The autonomous model still chooses the actions and arguments. Four new seeds 209–212 test this correction; further Nano capability failures trigger Super escalation rather than repeated tuning around Nano. The same settings apply to A and B. The provider API specification does not document sampling seed support; the sent seed is logged, but effective support remains unverified.

The forced-tool-choice batch at code `9ef3633b72ce69d25729f8aa2d75c464e296631b` completed **0/4**, with repeated data-generation calls causing budget rejection. Evidence remains under `artifacts/pilots/viability/20261004T163855Z-edf9174b`. The relative contribution of model capability and provider behavior under forced tool choice is unresolved. Automatic tool choice is restored to match the official cookbook pattern; the common prompt explicitly distinguishes native calls from prose/JSON.

Nano's automatic-tool-choice batch failed the 3/4 gate, so the next batch uses catalog-confirmed `nvidia/nemotron-3-super-120b-a12b`, seeds 213–216, with identical A/B settings. The [official model page](https://nebius.com/services/token-factory/models/nvidia-nemotron-models-inference) lists Super at $0.30/$0.90 per million input/output tokens; its ledger uses a conservative $2 per million for both under the same cumulative $20 cap. Super tokenizer data is pinned to NVIDIA revision `2dc98e2afe4face0e4ce40972a915c45368bd34a`, SHA-256 `623c34567aebb18582765289fbe23d901c62704d6518d71866e0e58db892b5b7`. No Ultra call has been made.

Real fine-tuning requires a supported small target with a verified deployment path and bounded cost. The [fine-tuning model guide](https://docs.tokenfactory.nebius.com/post-training/models) lists Qwen2.5-0.5B-Instruct, Qwen3-0.6B and Llama-3.2-1B-Instruct, but states that deployment currently uses dedicated endpoints. The authenticated templates do not establish an end-to-end deployment path for those small targets. Do not substitute a much larger target or submit an unbounded job to work around this gap.

Before claim runs: validate real training/deployment/evaluation, obtain real pilot cost and task-difficulty evidence, freeze the Arm C recipe and prediction baselines, commit preregistration with 12 paired seeds and `delta_min`, verify provider input-length behavior, then freeze code. H1 cannot be evaluated using Phase 2A synthetic scores.

Super seeds 213–216 at code `3ec18d30aa3cb701e3958286fadd43c5308c53e8` completed **2/4**. Both failures requested generation above the remaining cumulative limit. All registry chains verified; artifacts are preserved under `artifacts/pilots/viability/20261004T164240Z-2e8cb6fd`. Cumulative conservative accounting reached $0.290573 across 73 calls, with no unresolved holds.

The final viability revision exposes live budget limits in tool schemas, removes exhausted generation/training/dev tools, and exposes prediction only after candidate commit. Enforcement and caps are unchanged. Super seeds 217–220 completed 4/4. These pilot revisions cannot be reused as frozen formal experiments.
