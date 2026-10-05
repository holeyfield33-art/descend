# Provenance

## Repo Steward WP0 boundary repair (2026-10-05)

The Git invocation policy, offline doctor and new regression tests are original
local changes based on source `b59a470231ec99d33ba297204dec9d4844c563ee` and the
inventory checkpoint `1b7dad1668ce09dc4f5196675786149d04853e79`.
The user subsequently authorized repairing the discovered boundary and
continuing without continuation prompts. Git's official `git-diff` documentation
informed the separate `--no-textconv`/`--no-ext-diff` flags; no upstream source was
copied. No sibling checkout was modified or imported. The harmless helper
positive control runs only in the Linux namespace worker. New test fixtures
are owned synthetic code, not external evaluation answers.

Runtime pins reflect the actual supported environments: Linux Python 3.14.4
in `.python-version`, Windows Python 3.14.6 in `.python-version.windows`.
They are deliberately recorded separately, not represented as identical
interpreters. The dependency lock remains shared; source text is LF while
historical `artifacts/**` retains exact bytes.

## Controller-side Nemotron loop

The Phase 2A client adapts the pinned cookbook's `models/nemotron/run_nemotron.ipynb` OpenAI client/chat-completions pattern and `tool-calling/function_calling_1.ipynb` assistant/tool response sequence. Adapted code lives in `descend/controller/inference.py` and `descend/agents/nemotron.py`; the cookbook remains an unchanged sibling reference, never a runtime dependency. Descend adds its own explicit schemas, isolated relay, token/spend reservations and durable evidence handling. The existing copied MIT notice covers adapted cookbook patterns.

Agent selection was confirmed by authenticated `/v1/models`: `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Input matching uses NVIDIA tokenizer data from `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16`, revision `bf77c3174f68ad409e1c2aa60daeb46e32d1c606`, SHA-256 `c6021eb6847e682f89aa52d5eb6e8c7d902a23acfc8137e25211cf84828f1592`. Only JSON tokenizer data is downloaded; no weights or remote Python code are loaded. This tokenizer does not prove the provider uses an identical private chat wrapper.

Descend DM0 is a self-contained repository.

The separate local real-weight feasibility recipe adapts the standard Qwen Transformers loading/chat-template example and PEFT's documented `LoraConfig`/`get_peft_model`/`save_pretrained` workflow. Descend supplies its own bounded loop, assistant-only loss masking, source snapshots, deterministic exact-match evaluation and saved-adapter reload verification. See [local pilot disclosure](LOCAL_REAL_WEIGHT_PILOT.md). It is not a Token Factory training/deployment result.

Super escalation uses catalog-confirmed `nvidia/nemotron-3-super-120b-a12b` and tokenizer-only JSON from `nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16`, pinned revision `2dc98e2afe4face0e4ce40972a915c45368bd34a`, SHA-256 `623c34567aebb18582765289fbe23d901c62704d6518d71866e0e58db892b5b7`. Provider weight hashes remain unavailable and are recorded as null with a reason. Pilot targets, adapter bytes and scores are explicitly synthetic; they are not LoRA training artifacts. Preserved source snapshots bind actual checkout bytes rather than assumed Git line endings.

No dependency on MRN-CRS, Aletheia Core, Mneme, K1 Memory, Geometric Brain, Helios, or any other prior project.

Those projects are code books only. The prior project's initial provenance statement was recovered from the supplied archive; its historical reuse claims have not been independently audited.

All hashing uses standard SHA-256 and canonical JSON serialization implemented in-tree.

## Recovery source

Missing implementation, tests, scripts and documentation were restored from the user's `descend.zip` rather than reconstructed from completion reports. [VERIFICATION_REPORT.md](VERIFICATION_REPORT.md) records the archive hash and initial public state; [RECOVERED_FILES.txt](RECOVERED_FILES.txt) lists recovered paths. The protocol/boundary changes and their tests are local Descend implementations, described in [PROTOCOL_REPAIR_REPORT.md](PROTOCOL_REPAIR_REPORT.md).

## Nebius Token Factory cookbook

- Upstream: https://github.com/nebius/token-factory-cookbook
- Inspected commit: `c2e6a2a4651ba8fd126365d7bbcd2b5621acb040`.
- Local sibling checkout: `../token-factory-cookbook`, treated as read-only reference material.
- License: MIT, copyright 2025 Nebius B.V.; the notice is preserved in [licenses/nebius-token-factory-cookbook.MIT.txt](licenses/nebius-token-factory-cookbook.MIT.txt).
- Adaptation: `controller/token_factory.py` borrows the minimal chat-completion payload from `models/nemotron/run_nemotron.ipynb`, the function-call decoding pattern from `tool-calling/function_calling_1.ipynb`, and the fine-tuning job structure from `post-training/fine-tuning-1/fine_tune_llama.ipynb`. Current official docs supersede the notebook's learning-rate spelling and inform terminal-state handling. Tests verify offline contracts, not paid API execution.
- Evaluation examples and legacy `/v0/models` creation were inspected as reference only; neither was copied into an enabled live backend. [TOKEN_FACTORY_REFERENCE.md](TOKEN_FACTORY_REFERENCE.md) records confirmed patterns and unresolved deployment details.

Descend has no runtime import, dependency, submodule or service connection to the cookbook. No upstream files were edited and no upstream notebooks were run. Future substantial reuse must extend this disclosure.
