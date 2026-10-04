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

### Security status (Phase 1.6 partial)

| Claim | Status |
|-------|--------|
| **A** — Agent-facing API cannot mutate the hidden judge | **PASS** for the tested run-scoped tool API |
| **B** — Arbitrary agent code (under agent isolation permissions) cannot directly read/mutate controller-owned judge state | **PASS** relative to integrated Linux tests |
| **C** — Arbitrary agent code cannot make unrestricted external network calls | **PASS** relative to integrated Linux tests |

The fake worker runs in **Linux namespaces (`unshare`) + chroot**, as UID 65534 with no network. The controller stays outside and serves a bounded, run-scoped JSON pipe. The worker receives no controller object or hidden seed. Unsupported hosts fail closed; Windows runs protocol tests and skips Linux worker tests. The Dockerfile is not used by this runtime.

See [`docs/PROTOCOL_REPAIR_REPORT.md`](docs/PROTOCOL_REPAIR_REPORT.md) for repair results and [`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md) for the historical recovery audit. Public clean-checkout verification has passed. Phase 2A remains gated on the remaining prerequisites.

Release verification and current checkout evidence are recorded in [`docs/RELEASE_VERIFICATION.md`](docs/RELEASE_VERIFICATION.md). The original recovery/repair reports preserve their historical test counts.

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for Levels 1–3 and residual risks.

**No claim-bearing DM0 experiment has been run yet.** No live Nemotron/Nebius backend or GPU training is enabled.

### Token Factory reference

The official [Token Factory cookbook](https://github.com/nebius/token-factory-cookbook) was cloned alongside Descend as a read-only code book at commit `c2e6a2a4651ba8fd126365d7bbcd2b5621acb040`. Descend does not import it or require it at runtime. [`docs/TOKEN_FACTORY_REFERENCE.md`](docs/TOKEN_FACTORY_REFERENCE.md) records verified inference, training, LoRA/custom-model, deployment and evaluation patterns, including discrepancies between notebook examples and current docs. Small offline request helpers are adapted locally under `descend/controller/token_factory.py`; they do not send requests or enable a cloud backend.

Nemotron is the planned agent; the trainable target remains a separate unresolved model. Neither the older Nano plan nor the notebook's model selection establishes current account availability.

### Quick start

Fake A/B trials require Linux with root namespace/chroot privileges (for example, a dedicated WSL test environment). Root is used by the trusted launcher; worker code runs as UID 65534. Native Windows has no soft fallback. Real credentials must stay outside the worker workspace and runtime mounts.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
python scripts/run_fake_trial.py --arm A --seed 42
python scripts/run_fake_trial.py --arm B --seed 42
```

On native Windows, use `.venv\Scripts\python -m pip install -e ".[dev]"` and `.venv\Scripts\python -m pytest`. Agent trials require the Linux runtime described above. Registry verification is available with `python scripts/verify_registry.py <run_id> --registry ./registry_data`; chain validity alone does not prove completeness after truncation.

### Documentation

- [Architecture and trust zones](docs/ARCHITECTURE.md)
- [Experimental design and status](docs/EXPERIMENT.md)
- [Roadmap and phase gates](docs/ROADMAP.md)
- [Locked specification corrections](docs/SPEC_DELTA_V1_RC.md)
- [Source provenance and reference policy](docs/PROVENANCE.md)

### Spec deltas

[`docs/SPEC_DELTA_V1_RC.md`](docs/SPEC_DELTA_V1_RC.md)

### License

MIT
