# Descend

**Descend is an autonomous model-improvement laboratory with a judge the agent cannot touch.**

## DM0 — Evidence-backed autonomous model adaptation

**Core question:** Does evidence about a target model help an autonomous AI improve that model?

DM0 is **not** AGI, recursive self-improvement, literal self-modification, or proof of self-awareness.

### Arms

| Arm | Description |
|-----|-------------|
| **A** | Agent + evidence-backed target-model report |
| **B** | Same agent/tools/budgets; neutral length-matched content |
| **C** | Fixed scripted LoRA recipe; no agent |

### Security status (Phase 1.6)

| Claim | Status |
|-------|--------|
| **A** — Agent-facing API cannot mutate the hidden judge | **PASS** |
| **B** — Arbitrary agent code (under agent isolation permissions) cannot directly read/mutate controller-owned judge state | **PASS** (relative to tested threat model) |
| **C** — Arbitrary agent code cannot make unrestricted external network calls | **PASS** (network namespace empty) |

Isolation runtime on this reference host: **Linux namespaces (`unshare`) + chroot** (Docker preferred when available; not required for the tested claims).

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for Levels 1–3 and residual risks.

**No claim-bearing DM0 experiment has been run yet.** No Nemotron/Nebius/GPU integration in this phase.

### Quick start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/run_fake_trial.py --arm A --seed 42
python scripts/run_fake_trial.py --arm B --seed 42
```

### Spec deltas

[`docs/SPEC_DELTA_V1_RC.md`](docs/SPEC_DELTA_V1_RC.md)

### License

MIT
