# Repo Steward engineering run manual

Status: current prototype operating reference, 2026-10-05. The complete
act/evaluation/demo manual is pending implementation and measured verification.
WP0 resumed with the authorized [Git helper execution repair](STEWARD_BOUNDARY_REVIEW.md).
No new live call is
authorized by the earlier $20 ceiling: WP6 requires a written cost approval.

## Environment and installation

Run from the Descend root. Keep references as sibling codebooks only.
The baseline has `requirements-lock.txt` (pytest 9.1.1). Python is pinned to
3.14.4 for Linux in `.python-version`, and 3.14.6 for Windows in
`.python-version.windows`. They are separately identified runtimes. Build tools
are not fully locked. Run `python -m descend doctor` from the repository root
to check exact installed versions and record helper paths and the lock hash.
`--require-act` currently exits nonzero because WP3 is not implemented.

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
accounting, 118 calls, zero unresolved holds; this is not a billing receipt.

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
WP3 still needs the export-only act worker and tamper
checks; WP4 needs the attack matrix and independent red-team handoff. WP5 needs
the one-command offline demo and scanned static bundle. Those commands do not
exist yet, apart from the corpus commands above, so this manual provides no
pretend invocations for the remaining work.

WP6 requires written approval after the estimate. WP7 adds measured results,
fresh-clone evidence and the final complete manual. Human deploys the bundle
and creates the new repository. Follow the [extraction plan](STEWARD_EXTRACTION_PLAN.md)
only after receiving that destination and authorization.
