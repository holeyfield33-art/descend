# DM0 Specification Deltas — v1 Release Candidate

These four corrections supersede the corresponding draft text in `Descend_DM0_Spec.pdf`.
All other DM0 v1.0 design decisions remain unchanged unless implementation reveals a blocking contradiction.

## 1. Operational limits belong to BOTH A and B

The manifest treatment must contain only target-specific evidence.

Both arms A and B receive identical operational information, including:

- tool documentation
- allowed actions
- current budget counters
- wall-clock budget
- agent-token budget
- training-submission budget
- dev-evaluation budget
- maximum training tokens
- editable surfaces
- sandbox restrictions
- candidate-commit rules
- prediction-commit rules

Arm A additionally receives target checkpoint identity/hash, architecture, parameter count, tokenizer characteristics, adapter compatibility, baseline capability/failure profiles, and (later) modification lineage.

Arm B receives neutral length-matched text in place of the target-specific evidence.

Treatment:

- A = common operating information + target evidence
- B = common operating information + neutral matched text

## 2. H1 statistical direction is one-sided

Primary hypothesis:

> H₁: T_A > T_B

Use a pre-registered one-sided paired randomization/permutation test on

> dᵢ = T_{A,i} − T_{B,i}

Do not use a two-sided test while claiming a directional hypothesis.

Primary result also requires a pre-registered minimum practical effect size:

> mean(d) ≥ δ_min

`delta_min` is exposed in the preregistration/config file and marked **UNFROZEN** until pilot calibration.

H2 and H3 remain secondary. No additional claim-bearing hypotheses.

## 3. Claim run uses 12 paired seeds

Supersedes the draft’s 8-seed claim run.

Formal claim-bearing experiment uses **12 paired seeds**.

Each paired seed fixes (where supported): DSL/task-generation seed, train/dev/hidden split seed, dataset-generation seed, agent sampling seed, LoRA/training seed, evaluator seed.

These are separate seed roles, not one disclosed seed reused everywhere. Hidden-string generation uses an independent controller-private seed shared across paired arms. Replay metadata stays controller-owned.

A/B/C for seed *i* share the same underlying generated task family and starting target state.

Pilot seeds remain separate and may never be reused in the claim run.

Seed list is not hardcoded; the preregistration file holds the frozen list later.

## 4. Candidate/run identity expanded

Candidate/run identity must bind:

- H(base)
- H(adapter)
- H(training dataset)
- H(training config)
- H(agent transcript)
- H(evaluator code)
- H(controller code)
- H(promotion rule)

Also record separately where available: manifest hash, preregistration hash, DSL generator version/hash, runtime/container version, exact agent model ID, exact target model ID, backend/provider metadata.

Canonical JSON serialization before hashing. Standard SHA-256.

## Implementation status

These are scientific requirements, not a claim that every field is production-ready. The CPU harness still uses fake adapter/base/code identities and approximate token accounting; Arm B's actual length matching remains outstanding. The integrated boundary and five priority protocol repairs are covered in [PROTOCOL_REPAIR_REPORT.md](PROTOCOL_REPAIR_REPORT.md). The current contamination interface returns only a pass/fail flag, an explicitly requested policy that must be reflected in the final preregistration.
