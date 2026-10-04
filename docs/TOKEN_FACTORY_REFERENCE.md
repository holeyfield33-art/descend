# Token Factory reference and API verification

Reviewed October 3, 2026 (America/Los_Angeles). Verification here means inspection of official source and current documentation, plus offline contract tests. No account API, inference, training, model creation or deployment request was sent.

## Reference policy

The sibling `../token-factory-cookbook` checkout is a read-only code book:

- Origin: https://github.com/nebius/token-factory-cookbook.git
- Observed HEAD: `c2e6a2a4651ba8fd126365d7bbcd2b5621acb040`.
- No edits, environment installation or notebook execution in that checkout.
- No submodule, import, package dependency, service dependency or runtime path from Descend to it.
- Descend owns adapted code locally; attribution and the upstream MIT notice are in [PROVENANCE.md](PROVENANCE.md).

## Verified patterns and adaptation choices

| Area | Official example / current docs | Descend decision |
|---|---|---|
| Nemotron inference | [Minimal Nemotron notebook][nemotron] uses OpenAI `chat.completions.create`, `NEBIUS_API_KEY`, and `https://api.tokenfactory.nebius.com/v1/` | Adapt this small request shape; keep key/client on the controller; supply an output cap and exact controller-selected model ID. No agent SDK credentials. |
| Function calling | [Small function-calling notebook][tools] and [official guide][tool-doc] return function names/JSON arguments; the application executes tools and appends a tool response with its call ID | Decode proposals into `ToolSession.dispatch`'s existing run-scoped envelope. The model never receives or invokes the Controller object. Preserve assistant tool calls and corresponding `tool_call_id` messages in the future model loop. |
| Fine-tuning submission | [Fine-tuning notebook][ft] uploads files with purpose `fine-tune`; [current SFT guide][sft] specifies `/v1/fine_tuning/jobs`, `model`, `training_file`, optional `validation_file`, `seed`, and LoRA hyperparameters | Adapt file/job/checkpoint flow after Phase 2A. The offline body uses `learning_rate`, `n_epochs`, `lora`, and `lora_r`; do not upload hidden data or credential-bearing integrations. |
| Job monitoring/artifacts | [Current job schema][job-api] and [SFT guide][sft] expose status, events, checkpoint/result-file IDs and file contents | Poll with a controller deadline; terminal states are succeeded/failed/cancelled. Freeze downloaded bytes and their identities before judging. File paths from provider metadata require validation. |
| LoRA / custom-model creation | Cookbook notebook constructs `POST /v0/models` with `name`, `base_model`, and `source=job_id:checkpoint_id`; [current model support page][train-models] says deployment is via dedicated endpoints | **Legacy pattern, not currently verified for use.** The old `fine-tuning/deploy-custom-model` documentation URL returned 404. Do not assume the API itself is removed, and do not invent a replacement registration call. |
| Dedicated deployment | [Current API quickstart][deploy] lists `/v0/dedicated_endpoints/templates`, creates `/v0/dedicated_endpoints`, and uses returned `routing_key` for regional `/v1` inference | Choose a provider-returned template; do not hardcode GPU/model/flavor/region availability. The [creation schema][endpoint-api] includes `custom_weights_id`, but that field alone does not verify the custom-weight registration/upload workflow. |
| Evaluation | [Official Inspect smoke example][eval] uses Chat Completions, temperature zero and exact-answer scoring; its offline tests use a mock | Borrow minimal prediction/scoring patterns. Keep Descend's synthetic DSL grader and one-shot hidden judge controller-owned. Cookbook smoke tasks are connectivity checks, not DM0 benchmarks or hidden-set evidence. No Inspect dependency is needed now. |

## Discrepancies that must not be copied blindly

- The fine-tuning notebook uses `learning_rate_multiplier`; the current SFT guide and job schema use `learning_rate`. The offline helper follows the current documentation.
- The SFT guide's Python polling snippet loops *while status is in terminal states*, contrary to its surrounding instructions. `job_finished` defines terminal states correctly; future polling must continue while it is false and remain deadline-bounded.
- The job reference also describes `method.supervised.hyperparameters`. The helper uses the top-level `hyperparameters` shape documented by the SFT walkthrough, without sending two conflicting configurations. Check the chosen SDK version/service response before live use.
- The current cookbook's featured minimal model is `nvidia/Nemotron-3_5-Lightning`; Super/Ultra alternatives are listed. Nano examples remain in the tree but are not featured in that README. Retain Nano as an unresolved plan until an authenticated model-list check confirms the exact active ID for the account. Do not silently substitute a different agent in paired runs. See the [pinned Nemotron index][nemotron-index].
- [Fine-tuning support][train-models] lists small separate target candidates, including Qwen2.5 0.5B and Qwen3 0.6B variants, with LoRA support. This establishes documented training candidates, not an end-to-end deployment route or a frozen target choice. Confirm both before choosing the smallest practical target.
- The [custom-weights page][custom-weights] currently exposes navigation without a usable registration recipe in the fetched content. The [LoRA merge guide][merge] documents merging into base weights, including a MoE example, but does not establish that every candidate target supports that exact merge script or deployment template.

## What is implemented now

`descend/controller/token_factory.py` contains small, network-free request builders and a provider-tool-call decoder adapted from those official examples. Contract tests route a sample decoded proposal through the actual run-scoped dispatcher. The helpers do not construct an SDK client, read credentials, submit jobs, create models, deploy endpoints or register a new cloud tool.

The controller-side `inference.py` now adapts the minimal OpenAI client pattern for live Nano/Super calls. It records measured usage, reserves bounded spend before each request, disables retries and redirects, and keeps credentials outside isolated workers. Native proposals cross the narrow JSON relay. Live schemas expose remaining operational budgets, while the controller enforces them independently. Authenticated discovery confirmed both exact IDs; the earlier unresolved catalog note above describes the initial documentation review.

Real fine-tuning, checkpoint downloads, custom-weight registration and deployment remain gated on a verified small target and bounded account-specific prices. The offline helpers are not a completed real-training backend. See [Phase 2 status](PHASE2_STATUS.md) and [ROADMAP.md](ROADMAP.md).

[nemotron]: https://github.com/nebius/token-factory-cookbook/blob/c2e6a2a4651ba8fd126365d7bbcd2b5621acb040/models/nemotron/run_nemotron.ipynb
[nemotron-index]: https://github.com/nebius/token-factory-cookbook/blob/c2e6a2a4651ba8fd126365d7bbcd2b5621acb040/models/nemotron/README.md
[tools]: https://github.com/nebius/token-factory-cookbook/blob/c2e6a2a4651ba8fd126365d7bbcd2b5621acb040/tool-calling/function_calling_1.ipynb
[ft]: https://github.com/nebius/token-factory-cookbook/blob/c2e6a2a4651ba8fd126365d7bbcd2b5621acb040/post-training/fine-tuning-1/fine_tune_llama.ipynb
[eval]: https://github.com/nebius/token-factory-cookbook/tree/c2e6a2a4651ba8fd126365d7bbcd2b5621acb040/evaluations/inspect-ai
[tool-doc]: https://docs.tokenfactory.nebius.com/ai-models-inference/function-calling
[sft]: https://docs.tokenfactory.nebius.com/post-training/how-to-fine-tune
[job-api]: https://docs.tokenfactory.nebius.com/api-reference/fine-tuning/create-a-fine-tuning-job
[train-models]: https://docs.tokenfactory.nebius.com/post-training/models
[deploy]: https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/deploy-api
[endpoint-api]: https://docs.tokenfactory.nebius.com/api-reference/dedicated-endpoints/create-dedicated-endpoint
[custom-weights]: https://docs.tokenfactory.nebius.com/ai-models-inference/dedicated-endpoints/custom-weights
[merge]: https://docs.tokenfactory.nebius.com/post-training/merge-moe-lora-weights
