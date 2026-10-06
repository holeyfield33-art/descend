# Vibe Explainer review of Descend (2026-10-05)

This is an analyst review of an offline static report, not a vulnerability assessment or an endorsement of Vibe's uncalibrated scores. No experimental scoring was enabled. The complete JSON and Markdown reports are private under `controller_state/vibe-descend-source-report.{json,md}` because even redacted reports can contain sensitive excerpts. They are intentionally not committed.

## Reproducible scope

- Vibe Explainer checkout: `5adbd44`, version `0.2.0a1`; its clean-checkout suite passed **403 tests**, with 7 skips and 50 subtests.
- Descend snapshot: clean Git commit `d9fc48964cde88aaadbd624ed44f9a3ca2832adf`. A sparse checkout included `descend/`, `scripts/`, `tests/`, `configs/`, `docs/` and root files. Tracked historical `artifacts/`, the live `.env`, local controller state and the nested codebook were not scanned.
- ASI catalog: local `asi-catalog.json`, version `0.2.0-draft`, Vibe source identity `sha256:9185745743107b97e68d34e20087204c46db2bd5a8dc41240446b70c3cf68bb1` (Vibe hashes filename, NUL, file bytes, NUL). No network catalog lookup.
- Source-focused JSON report SHA-256: `a1cd96b4c7c111f80015c998f4af8c85eaa1bdb3075d085391dd74e3bf8f488c`. Vibe reported 131 discovered, 126 inspected and 5 skipped files, 375,128 inspected bytes, no budget exhaustion or parse failures, and `inventory_complete=true`. Its assessment status was `AGGREGATED`, not a runtime proof.

The first full-tree scan was misleading for current-code review: tracked pilot artifacts copied earlier versions of controller code. It counted 139 AI/surface leads and repeated model-call sites. The source-focused scan counted **33 leads** and two current model-call sites. The two scopes answer different questions; do not add their counts or describe copied pilot code as additional live surfaces.

## Report adjudication

| Vibe observation | Analyst reading |
|---|---|
| One unscored `OUTPUT_SECURITY` concern, reachability `NOT_ESTABLISHED`; C04 output handling `NOT_FOUND` at `descend/controller/inference.py` and `descend/steward/reviewer.py` | A useful prompt for review, not evidence of an unsafe sink. The steward parses model JSON and checks quoted added lines in `descend/steward/findings.py`; the DM0 tool path validates proposed function names/arguments and controller actions in other modules. Vibe's static relationship pass did not join those cross-file steps. Output validation is real but limited: exact citation matching does not prove a model's bug claim. |
| C05 tool authorization `PARTIAL`; C12 high-risk action controls `NOT_FOUND` | Vibe grouped trusted Git subprocess calls, tests, and namespace/chroot setup with agent-requested actions. The steward's Git call uses an argument vector and timeout; the DM0 worker boundary and controller-side tool dispatcher impose separate controls. Vibe did not prove these calls are agent-controlled or unguarded. Review each call path before upgrading the concern. |
| C06 human approval `NOT_FOUND` | Current steward autonomy is read-only: scan, paid inference within the durable cap, and local display. Maintainer triage is manual. No agent patch/push tool exists, so lack of an approval gate on such a tool is not a current exploit. A future patch executor needs an explicit, narrow approval/authorization check. |
| C07 auditability `NOT_FOUND` | Descend DM0 has anchored registry records; Repo Steward stores reviews, provider IDs, usage and decisions in SQLite. Neither establishes tamper-evident audit for the steward. That is a product improvement, while the blanket absence claim misses existing records. |
| Process testing `NOT_OBSERVED` | False negative for this checkout: `tests/adversarial_agent/` and other boundary/contract tests exist. A named `tests/security/` directory or CI workflow may still be absent; Vibe's path heuristic is narrower than the actual test suite. |
| ASI: 40 draft classes, 20 protocol-applicable, **0 class-specific evidence observed** | “Applicable” means native model/tool integration appears in the repository. It does not mean 20 attacks exist. Class rows require separate evidence and analyst review; the catalog's mitigations remain unvalidated research entries. |

Independent code review also flags a limitation Vibe did not establish: Repo Steward's `SECRET_PATH`/`SECRET_LINE` filters are best-effort patterns, not a guarantee that a watched commit is safe to upload. `--live` must remain an explicit choice on a repo whose code may be sent to Token Factory. The watcher reviews only the latest commit at each poll; intermediate commits can be missed when several land between scans.

## Giving Repo Steward Vibe and ASI context

Vibe already accepts `--asi-catalog`; no direct ASI query or second taxonomy implementation is needed. Run Vibe **controller-side**, offline, on a clean snapshot of the exact commit and retain its full report locally. An optional Repo Steward adapter (`descend/steward/vibe_context.py`) now checks Vibe schema 2.0, clean matching commit, complete inventory and the exact ASI catalog identity. It passes only bounded lead IDs/titles/statuses and ASI counts to Nemotron, with a warning that these are static leads. It does not forward raw report excerpts or treat protocol applicability as attack evidence. The structured review still needs an added-line citation, and the maintainer still decides whether the claimed bug is real.

Example, with Vibe installed in its own environment and a clean checkout at the watched commit:

```powershell
python -m vibe_explainer <clean-descend-checkout> --json --asi-catalog <asi-catalog.json> --out <private-report.json>
python -m scripts.run_repo_steward --repo <descend-checkout> --live --once --vibe-report <private-report.json> --asi-catalog <asi-catalog.json>
```

The Vibe package, ASI export and cookbook can stay separate; Descend's normal runtime has no dependency on the sibling source checkouts. For an always-on product, run Vibe only after a new commit and cache the report by repository, commit, scanner version, configuration and catalog hash. A tool failure or partial report should be visible as `unavailable` and should not silently become a clean bill of health. Do not upload the full report to the model without a separate disclosure decision.

One bounded combined pilot reviewed Descend commit `d9fc489` with this static context. Nemotron made one citation-valid but substantively false claim: it called strict built-in `int` validation an error, even though that rule intentionally rejects `bool` and unsupported numeric subclasses. The finding was marked `dismissed` in SQLite. This is evidence that citation validation and a real maintainer decision remain necessary after ASI/Vibe enrichment. Provider usage was 2,991 input and 163 output tokens; conservative accounting added **$0.006308**, taking the cumulative ledger to **$0.548195 across 118 calls**, with no unresolved holds.

## What “multiple repositories need to be configured” means

The original `run_repo_steward.py` takes one `--repo` path per process. `run_repo_steward_fleet.py` now reads an explicit JSON allowlist of repository roots, mock/live modes, intervals and optional paired Vibe/ASI paths. A private local configuration at `controller_state/steward-repos.json` lists Descend, Vibe Explainer and Agent Security Index in **mock mode**; `configs/steward-repos.example.json` is a portable example. One no-cost `--once` pass scanned all three. A shared SQLite store and dashboard collect results. No watched repository is changed by the fleet runner.

This is a first configuration layer, not a complete multi-repo release. It still reviews **only each checkout's latest commit**, so intermediate commits can be missed between polls; mock/live upload policy is explicit but per-repo spend caps, persisted commit cursors and richer dashboard health are absent. Every new commit should eventually be queued in order with a per-repository cursor and a clear policy for force-pushes and skipped commits.
# Current phase notice

Further Vibe/ASI integration and fleet development are parked by the new
Repo Steward directive. This report remains historical pilot evidence.
The completed [Git boundary repair](STEWARD_BOUNDARY_REVIEW.md) and
[phase report](STEWARD_PHASE_REPORT.md) take precedence over earlier next steps.
