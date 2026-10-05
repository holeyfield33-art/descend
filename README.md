# Descend

## Repo Steward development status — 2026-10-05

Repo Steward's WP0 inventory and baseline gate is complete: fresh public clones
passed 125 Linux tests and 100 Windows tests (25 explicit skips).
The watcher Git helper-execution issue has been repaired and tested with an
isolated positive control. See the [finding and repair](docs/STEWARD_BOUNDARY_REVIEW.md).
New paid calls require
the directive's separate WP6 approval; the existing $20 ceiling is not that approval.

The [phase report](docs/STEWARD_PHASE_REPORT.md),
[engineering operating reference](docs/STEWARD_RUN_MANUAL.md),
[interface inventory](docs/STEWARD_INVENTORY.md) and
[extraction plan](docs/STEWARD_EXTRACTION_PLAN.md) describe the current state.
The complete act slice, frozen evaluation and offline demo remain pending.
No extraction has occurred; the new repository will be supplied by the user.
The DM0 evidence below concerns its separate worker boundary.

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

### Tested security boundary

| Claim | Status |
|-------|--------|
| **A** — Agent-facing API cannot mutate the hidden judge | **PASS** for the tested run-scoped tool API |
| **B** — Arbitrary agent code (under agent isolation permissions) cannot directly read/mutate controller-owned judge state | **PASS** relative to integrated Linux tests |
| **C** — Arbitrary agent code cannot make unrestricted external network calls | **PASS** relative to integrated Linux tests |

The fake worker runs in **Linux namespaces (`unshare`) + chroot**, as UID 65534 with no network. The controller stays outside and serves a bounded, run-scoped JSON pipe. The worker receives no controller object or hidden seed. Unsupported hosts fail closed; Windows runs protocol tests and skips Linux worker tests. The Dockerfile is not used by this runtime.

See [`docs/PROTOCOL_REPAIR_REPORT.md`](docs/PROTOCOL_REPAIR_REPORT.md) for historical repair results and [`docs/VERIFICATION_REPORT.md`](docs/VERIFICATION_REPORT.md) for the recovery audit. The Phase 2A launcher adds paired report matching, a full runtime dependency lock, registry head anchors, real local artifact/code hashes and measured provider usage.

Release verification and current checkout evidence are recorded in [`docs/RELEASE_VERIFICATION.md`](docs/RELEASE_VERIFICATION.md). The original recovery/repair reports preserve their historical test counts.

See [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md) for Levels 1–3 and residual risks.

**No claim-bearing DM0 experiment has been run yet.** A budgeted Nemotron inference launcher is available for Phase 2A viability with fake training. Real target training and deployment remain gated.

### Token Factory reference

The official [Token Factory cookbook](https://github.com/nebius/token-factory-cookbook) was cloned alongside Descend as a read-only code book at commit `c2e6a2a4651ba8fd126365d7bbcd2b5621acb040`. Descend does not import it or require it at runtime. [`docs/TOKEN_FACTORY_REFERENCE.md`](docs/TOKEN_FACTORY_REFERENCE.md) records verified inference, training, LoRA/custom-model, deployment and evaluation patterns, including discrepancies between notebook examples and current docs. Small offline request helpers are adapted locally under `descend/controller/token_factory.py`; they do not send requests or enable a cloud backend.

Authenticated catalog discovery confirmed Nano (`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`) and Super (`nvidia/nemotron-3-super-120b-a12b`). Real inference pilots have run with fake training/scoring; failed attempts remain preserved. The trainable target remains a separate unresolved model. See [Phase 2 status](docs/PHASE2_STATUS.md). Audit saved evidence offline with `python -m scripts.audit_viability`.

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

### Controller environment

Store local settings in the Git-ignored `.env` using active `NAME=value` lines. A leading `#` comments out a setting; PowerShell `$env:NAME=...` commands do not belong in this file. Validate and load settings into a Python controller process without printing values or making requests:

```bash
python -m descend.controller.environment --env-file .env --check
```

Controller entry points explicitly call `load_controller_environment` from `descend.controller.environment` before creating a provider client. Existing process variables take precedence. This does not change the parent terminal's environment. The isolated worker keeps its separate clean environment. The authorized cloud-spend ceiling is $20, enforced by controller-owned durable inference reservations. Unpriced training/deployment operations are disabled.

For Phase 2A, on the privileged Linux controller host, install `requirements-lock.txt` and then `pip install --no-deps -e .`. From a clean Git checkout with controller credentials configured:

```bash
python -m scripts.provider_preflight
python -m scripts.prepare_tokenizer --model super
python -m scripts.run_nemotron_viability --model super --seed-start 221
```

Each viability invocation makes paid inference calls and preserves a separate four-attempt batch under `artifacts/pilots/viability/`. **The Super batch at seeds 217–220 passed 4/4**; no further viability call is required for that gate. Seeds 201–220 are already used for viability and cannot be reused. The launcher requires an explicit unused seed range. Live schemas and counters expose remaining budgets, and NVIDIA's reasoning-off request setting is recorded. The pinned tokenizer matches input-content lengths; the successful Super batch's provider prompt totals differed by one token between arms, an unresolved prerequisite for formal runs. All training/scoring in these pilots is fake; no synthetic score supports H1. Evidence retains exact bytes across Git checkouts.

### Documentation

The first local real-weight target was Qwen2.5-0.5B-Instruct. A separate CPU feasibility pilot avoids unpriced cloud operations; its backend choice, task-definition correction and failed calibration results for Qwen2.5-0.5B and Qwen3-0.6B are disclosed in [the local pilot notes](docs/LOCAL_REAL_WEIGHT_PILOT.md). Neither target met the 25–60% base-difficulty gate under tested recipes. This work supplies no formal DM0 data and does not verify Token Factory training deployment.

- [Architecture and trust zones](docs/ARCHITECTURE.md)
- [Experimental design and status](docs/EXPERIMENT.md)
- [Roadmap and phase gates](docs/ROADMAP.md)
- [Hackathon Repo Steward product direction](docs/HACKATHON_REPO_STEWARD.md)
- [Vibe Explainer and Agent Security Index review](docs/VIBE_EXPLAINER_REVIEW.md)

Repo Steward now has a read-only prototype: `python -m scripts.run_repo_steward --repo /path/to/git-checkout --once` records a no-cost mock scan; add `--live` to request a bounded Nemotron Super review through the controller spend ledger. Run `python -m scripts.view_repo_steward` to see validated diff citations at `http://127.0.0.1:8765/`. A local triage CLI stores confirmed/dismissed maintainer decisions. The dashboard checks citation provenance, not bug correctness. Commands are documented in the linked product direction; this remains a prototype, not a complete hackathon submission.

For several checkouts, use the explicit [fleet configuration example](configs/steward-repos.example.json) with `python -m scripts.run_repo_steward_fleet --config <your-private-config.json> --once`. Each entry has its own mock/live mode and polling interval. The optional Vibe/ASI report input is described in the [analyst review](docs/VIBE_EXPLAINER_REVIEW.md).
- [Locked specification corrections](docs/SPEC_DELTA_V1_RC.md)
- [Source provenance and reference policy](docs/PROVENANCE.md)

### Spec deltas

[`docs/SPEC_DELTA_V1_RC.md`](docs/SPEC_DELTA_V1_RC.md)

### License

MIT
