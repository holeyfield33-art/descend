# Descend Architecture (DM0)

## Trust Zones

### Zone 1 — Agent Sandbox
Writable by the agent. Scratch files, proposed datasets, scripts, notes, configs.
No raw credentials. No unrestricted network.

The executable fake worker runs as UID 65534 in a Linux chroot with new mount, PID and network namespaces. Only its workspace and limited `/tmp` are writable; system runtime mounts are read-only. The trusted host launcher may hold the controller, but the worker receives only serialized manifest content and pipes. Native Windows has no soft fallback for agent execution.

### Zone 2 — Controller
The judge. Owns hidden examples, hidden seeds, evaluator, promotion rule, preregistration, manifest generation, budget enforcement, candidate validation, hidden evaluation.
The agent cannot read or write controller internals.

`sandbox/transport.py` binds one JSON pipe to one run and an explicit tool allowlist. It handles permitted generation, fake training, capped dev feedback, commitments and filtered registry reads. Hidden evaluation and promotion are controller-only. Rejected requests count toward budgets; a breach halts the worker. Predictions are copied and frozen, and the decision reads the verified frozen bytes. Hidden strings use a private seed independent of the public DSL seed; paired runs share the private seed under controller ownership.

`controller/token_factory.py` prepares offline request bodies from pinned official examples. It has no network client, credentials or cookbook imports and is not an enabled cloud backend. Future external calls must execute on the controller side with measured usage and the same run policy. The sibling cookbook is a read-only code book, not a service or runtime dependency.

### Zone 3 — Registry
Controller-written. Append-only. Hash-chained.
Agent may receive a read-only view of its own run history; cannot append or modify.

Agent views use an event/field allowlist and exclude hidden results, decisions and backing-chain hashes. Contamination feedback is only a pass/fail flag, per the current user-approved policy. An independent controller-owned head/count anchor detects log truncation; it does not protect against a compromised controller rewriting both files. Legacy unanchored logs fail verification.

## Arms

- **A**: Nemotron (or fake) agent + evidence-backed target-model report
- **B**: Same agent, tools, budgets, task, operational info; neutral length-matched content instead of target evidence
- **C**: Fixed scripted LoRA recipe; no agent

## One-shot Hidden Evaluation

dev optimization → candidate commit → prediction commit → hidden evaluation → PROMOTE/REJECT

Agent receives capped dev evaluations only. Never receives hidden examples, labels, scores, or promotion outcome during optimization.

Optimization closes at candidate commitment. Prediction commitment follows once; hidden evaluation follows once outside the worker. A/B length matching and real artifact/code identities remain prerequisites for claim-bearing experiments. See [current threat model](THREAT_MODEL.md), [repair report](PROTOCOL_REPAIR_REPORT.md), and [Token Factory reference](TOKEN_FACTORY_REFERENCE.md).
