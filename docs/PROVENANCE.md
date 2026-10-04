# Provenance

Descend DM0 is a self-contained repository.

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
