# DM0 Experiment

## Core Question

Does evidence about a target model help an autonomous AI improve that model?

## What DM0 Is Not

- Not AGI
- Not recursive self-improvement
- Not literal self-modification
- Not proof of self-awareness

The agent modifies a **separate** target model.

## Primary Hypothesis

H₁: T_A > T_B

One-sided paired randomization test on paired differences.
Minimum practical effect size δ_min (UNFROZEN until pilot).

## Claim Run

12 paired seeds (not 8).

## Status

No claim-bearing DM0 experiment has been run yet.
CPU-only fake-agent harness is the current milestone.

The recovered Phase 1.6 harness now tests an integrated isolated fake worker, run-scoped tools, frozen predictions and budget enforcement. Its training and scores remain hash-derived fixtures; PROMOTE in a fake trial is not measured improvement.

The formal design requires paired A/B task families and independently controlled hidden-string seeds. The private hidden seed is replay metadata owned by the controller, never an agent tool parameter. Agent-facing contamination feedback is currently a bare pass/fail flag; detailed overlap and hidden scores are excluded. This flag policy is an explicit departure from a strict zero-information contamination policy and must be documented before preregistration.

Agent and target remain separate. Nemotron availability and target training/deployment compatibility must be checked from the current provider catalog before selection. The read-only cookbook informs API preparation, not experimental evidence. See [roadmap](ROADMAP.md), [current API findings](TOKEN_FACTORY_REFERENCE.md), and [release verification](RELEASE_VERIFICATION.md).

Actual A/B length matching, complete identities, artifact-byte freezing and final confidence/regression rules must be verified before pilots become a claim-bearing run. `delta_min` and claim seeds remain UNFROZEN until pilot calibration; pilot seeds must not be reused.
