# Repo Steward engineering run manual

Status: offline act/evaluation/demo operating manual, 2026-10-06.
Live comparative evaluation is complete; independent red-team review and human
adjudication remain pending. Read STEWARD_LIVE_RESULTS.md before using the scores.
WP0 resumed with the authorized [Git helper execution repair](STEWARD_BOUNDARY_REVIEW.md).
The user approved frozen plan v4 on 2026-10-06: $8 additional cap, $6.40 stop
threshold, cumulative ceiling $20. This approval covers only that workload.

## Environment and installation

Run from the Descend root. Keep references as sibling codebooks only.
The baseline has `requirements-lock.txt` (pytest 9.1.1). Python is pinned to
3.14.4 for Linux in `.python-version`, and 3.14.6 for Windows in
`.python-version.windows`. They are separately identified runtimes. Build tools
are not fully locked. Run `python -m descend doctor` from the repository root
to check exact installed versions and record helper paths and the lock hash.
`--require-act` runs a benign test through the actual Linux x86_64 worker and
requires its syscall filter. It passed in the recorded Linux public-clone check;
native Windows fails closed for act execution.

For a trusted clean checkout, the existing installation sequence is:

```powershell
py -m venv .venv
.venv\Scripts\python -m pip install -r requirements-lock.txt
.venv\Scripts\python -m pip install --no-deps -e .
```

Linux uses `python3 -m venv .venv`, `.venv/bin/python -m pip` with the same
arguments. Prefer a WSL-native checkout. Linux worker execution requires
namespace/chroot privileges; Windows must never run generated tests directly.
Dependency installation is a setup network operation, not a model call.

## Credentials and spend

Keys belong only in the controller environment or ignored `.env`. Literal
`NAME=value` syntax is supported; PowerShell commands do not belong in `.env`.
Existing process values take precedence. To check without displaying values:

```powershell
.venv\Scripts\python -m descend.controller.environment --env-file .env --check
```

The shared ledger is `controller_state/cloud-spend.sqlite`. Do not delete it,
reset reservations, or create a substitute ledger to bypass accounting.
An ambiguous failure keeps its reservation. Reconcile with provider records
before authorizing more spend. Recorded session total: $0.548195 conservative
accounting before the live run, 118 calls. After the approved run: $0.613690,
223 calls, zero unresolved holds; this is not a billing receipt.

## Existing review operations

For an explicitly selected owned checkout, a transport-only scan uses:

```powershell
.venv\Scripts\python -m scripts.run_repo_steward --repo C:\absolute\owned-checkout --once
```

It records mock output with no AI review. Omit `--once` for polling; minimum
interval is 10 seconds. Only latest HEAD is reviewed against its first parent;
intermediate commits and working-tree edits are not traversed. `--live` is the
paid mode and is reserved for the approved WP6 run in this phase. Do not enable
it merely because a key exists.

Mock DB: `controller_state/steward-mock-v2.sqlite`. Live DB:
`controller_state/steward-reviews-v2.sqlite`. Claims use repository path plus
commit SHA. Cached results do not make another call. `error` and `in_progress`
are sealed against automatic retries; investigate rather than deleting rows.

View existing local data without a scan:

```powershell
.venv\Scripts\python -m scripts.view_repo_steward --db controller_state/steward-mock-v2.sqlite --port 8765
```

Open `http://127.0.0.1:8765/`. Keep loopback-only; this is not the public static
demo. The CLI opens/creates the DB if absent. Ctrl+C stops the server or watcher.
Do not publish raw SQLite state: it can contain private source and paths.

Record a maintainer decision on an existing live finding:

```powershell
.venv\Scripts\python -m scripts.triage_repo_steward --repo C:\absolute\owned-checkout --sha FULL_LOWERCASE_40_CHARACTER_SHA --finding 0 --decision dismissed --note "Reason for decision"
```

Use `--db` for a different store. `confirmed` is also supported. This records a
human judgment; it neither proves a bug nor authorizes a patch. Citations may
be corrected only by unique exact added-line matching. Unsupported citations
are withheld. No apply, push, PR or generated-code execution tool exists here.

## Verification and future delivery gates

Record the full output of
`.venv\Scripts\python -m pytest -ra` on Windows and
`.venv/bin/python -m pytest -ra` in WSL. Record collected/passed/failed counts
and each skip reason. Windows Linux-only skips are not security passes.
Repeat from a fresh public clone, recording SHA, Python, helper paths and lock
hash. Current execution evidence is in the phase report.

WP1 now has a frozen corpus and 68 successful isolated label checks. Rebuild
without executing fixtures using `python -m scripts.build_steward_corpus --output
controller_state/corpus-rebuild` (the output directory must be empty). See
[`eval/README.md`](../eval/README.md) for the pinned Linux pytest runtime setup
and `python -m scripts.check_steward_corpus --output controller_state/corpus-validation.json`.
The checker refuses native Windows. Frozen hashes and full per-case evidence
are recorded in the phase report. Never send labels, fixes or reproducers to
the reviewer. WP2 now has scoring, B0/B1 and blind adjudication-sheet exports.
Provision `requirements-steward-eval-lock.txt` into the trusted Linux pytest
runtime, then run `python -m scripts.run_steward_baselines --output
controller_state/steward-baselines-v1`. Score each arm with
`python -m scripts.score_steward_results --results controller_state/steward-baselines-v1/B1.json
--output controller_state/B1-test --split test`. B0 uses the same command with
its exported filename. Scores include every miss/error; blind sheets exclude
model/case labels and their mappings remain separate. Never present automatic
location matching as human-adjudicated accuracy. See `EVALUATION.md`.
WP3 provides the restricted export-only act worker and tamper checks; see
[`STEWARD_ACT.md`](STEWARD_ACT.md) for schema, scope, limits, proposal and corpus
commands. `doctor --require-act` executes a benign test through the actual
Linux worker and requires its syscall filter. It is not a red-team grade.
WP4's [attack matrix](STEWARD_ATTACK_MATRIX.md) and
[independent handoff](STEWARD_REDTEAM_HANDOFF.md) document coverage and limits.

For WP5 run `python -m scripts.demo_steward --output controller_state/new-demo`
in provisioned Linux/WSL, from the repo root. Use a new output directory and
run serially. Expect `complete: true`, `PATCH_VERIFIED`, zero provider calls,
checkout unchanged and repeated action claim false. Native Windows refuses;
the committed static bundle is a recorded mock view. See [demo details](STEWARD_DEMO.md).
Publish only the generated `public/` directory after checking its hash manifest
and LICENSE. Never publish the SQLite stores, `.env` or controller scratch.
The bundle has no action tools and deployment remains a human task.

Troubleshooting: a false `act_ready` means stop execution and inspect the probe's
error, helper paths, Linux x86_64 architecture, root namespace privileges and
the pinned runtime under `/usr/local/lib/steward-test-runtime`. No soft fallback
is available. ERROR/TAMPERED results export no applicable patch. Existing action
claims remain sealed after failure; do not erase state to retry a paid action.
Check watched Git status and exact SHA before human patch application, then run
the repository's normal validation. A recorded approval note is not execution
authority and a model statement that tests passed is not evidence.

WP6 requires written approval after the estimate.

Archived WP6 readiness check (no environment/client reads):

```bash
python -m scripts.run_steward_live --plan eval/steward-live-plan-v4.json --check
```

Only after the human approves the exact plan/cap, save that approval as a
controller-only text file containing `APPROVE PLAN <plan_sha256> CAP_USD 8`.
Do not manufacture approval. The completed workload's command is shown as an
operating reference. Do not rerun v4: its corpus claim is sealed. A future
workload needs a separate unseen dataset, frozen configuration, current ledger
estimate and new written approval.

```bash
python -m scripts.run_steward_live --plan eval/steward-live-plan-v4.json --approval controller_state/live-approval.txt --output controller_state/new-live-results
```

It probes Linux isolation, checks hashes/ledger, claims both plan and frozen
corpus once, and only then loads the controller key and constructs the client.
Output must be new. Do not reset claims after an error or change prompts after
the first test call. Use the raw records to investigate; no automatic resume.
Primary model JSON, Wilson scores, blind sheets, variance rows, act cards,
usage/provider IDs and errors remain local until a separate public-data review.
The proposed cost assumptions and cap are in [the plan](STEWARD_LIVE_PLAN.md).

WP7 adds measured results,
fresh-clone evidence and the final complete manual. Human deploys the bundle
and creates the new repository. Follow the [extraction plan](STEWARD_EXTRACTION_PLAN.md)
only after receiving that destination and authorization.

## Completed live run and public export

The approved v4 workload ran once on 2026-10-06: 104 review calls plus one
proposal, then a fail-closed act halt. Never repeat it or clear corpus claims.
The source JSON preserves the original proposed status; separate approval and
execution evidence establish its completed state. No remaining budget authorizes
a second workload. Raw owned-fixture responses, request hashes, usage and all
errors are preserved under `docs/evidence/steward-live-20261006/`.

To regenerate the read-only live report/bundle without keys or network:

```bash
python -m scripts.export_steward_evaluation --source docs/evidence/steward-live-20261006 --output controller_state/new-live-export
```

Output must be new. The exporter rejects unowned cases and sensitive patterns
before writing, escapes HTML, copies LICENSE and creates a hash manifest under
a 500 KiB cap. Publish only `public/`; human deployment remains pending. The
committed live bundle is `docs/evidence/steward-live-public/`; the older demo
bundle remains explicitly mock. No static bundle includes approval, SQLite or
environment files. Human adjudication sheets are exported separately; review
them without the model/label mapping before recording semantic judgments.
