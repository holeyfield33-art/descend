# Repo Steward inventory

## WP1 planned interfaces (recorded before implementation/testing)

`scripts.build_steward_corpus.main` and `descend.steward.corpus.build_corpus`
write owned generated Python snapshots, diffs, reproducers and JSON manifests
under a caller-selected empty output directory. No generated source is imported
or executed by the generator. `verify_manifest` reads bytes and checks hashes.
`scripts.check_steward_corpus.main` reads frozen manifests and copies each owned
fixture into a new scratch directory; invokes only the Linux isolated worker,
then writes bounded test results/hashes to an explicit report path. The worker
runs a controller-selected pinned pytest argv, never a fixture-selected command.
No provider, credentials, sibling imports, Git mutation or checkout patching.
Ground truth stays in evaluator manifests, separate from future review inputs.
The worker pytest runtime is trusted installed package code under a read-only
system runtime mount; it is not a controller asset store.

Worker compatibility addition: the trusted wrapper bind-mounts only `/dev/null`
inside its new chroot before dropping UID.
Git otherwise refuses even `init` in the minimal worker. No host device tree
is mounted and no controller path becomes visible. The isolated Git positive
control exercises this addition; existing isolation tests are retained.

WP0 diagnostics extension: `doctor.diagnose(root)` reads `.python-version`,
`requirements-lock.txt` and installed package metadata, resolves helper paths,
and calls the existing namespace prerequisite probe. `descend.__main__.main`
exposes `python -m descend doctor` / installed `descend doctor`, with `--root`
and fail-closed `--require-act`. Writes JSON to stdout only; no credentials,
provider calls, target execution or filesystem mutation. Tests will validate
missing dependencies and act refusal; act readiness remains false until WP3.

Repair extension: `watch.git_environment()` constructs a minimal process
environment without credentials or inherited Git overrides; `_git` pins the
resolved executable, disables fsmonitor/hooks/protocols/replacement objects,
and all diff paths disable textconv/external diff/submodule recursion. Reads:
trusted process PATH at module import and Windows SystemRoot only. Writes:
none beyond existing Git reads. Tests: `test_steward_git_boundary.py`.

WP0 static inventory, 2026-10-05. Source: `b59a470231ec99d33ba297204dec9d4844c563ee`.
Inventory precedes new tests. This is an interface and data-flow inventory,
not a claim of test coverage or security assurance. See the open
[Git boundary finding](STEWARD_BOUNDARY_REVIEW.md).

## Modules and callable surfaces

| Module | Public methods / entry points | Reads, writes, boundary |
|---|---|---|
| `descend/steward/__init__.py` | Package marker | No operational IO |
| `watch.py` | `commit_snapshot`, `scan_once`; `ReviewStore.__init__`, `get`, `claim`, `update`, `recent`, `decide` | Reads Git checkout metadata/objects/config/attributes through `_git`; creates DB parent and tables; claims/reviews/decisions stored in SQLite; repo bytes cross into controller and later provider prompt |
| `findings.py` | `added_lines`, `validate_findings` | In-memory diff and model JSON; validates added-line citations, can correct uniquely matching line; no disk or network; citation validity is not bug validity |
| `reviewer.py` | `review_with_nemotron` | One `client.chat.completions.create` site; sends bounded snapshot/context via Token Factory; reserves/settles shared ledger; returns raw response, usage, citations; controller holds key |
| `dashboard.py` | `render_reviews`, `serve_dashboard`, nested `Handler.do_GET` | Reads `ReviewStore.recent`; escaped HTML; HTTP GET on loopback, CSP/no-store; no mutation endpoint; server request logging to stderr |
| `fleet.py` | `load_fleet` | Reads explicit JSON config, resolves allowlisted directory/context paths; validates modes/intervals; no runtime sibling imports; parked |
| `vibe_context.py` | `load_vibe_context` | Reads report and exact ASI catalog bytes; checks schema/clean commit/completeness/catalog hash; summarizes bounded leads and counts into prompt context; parked |

Private `_git` is included because it is the execution boundary: subprocess
argv, inherited environment, captured output, 20-second timeout. Output is
captured before the 12,000-byte diff limit. It currently resolves `git` from
PATH, rather than pinning an absolute executable. The helper-execution finding
is open. Size limits after capture are not memory bounds on the subprocess.

## CLI surfaces

Each module below exposes `main()` and supports Python `-m` invocation.

| Script | Inputs / flags | Effects |
|---|---|---|
| `scripts/run_repo_steward.py` | `--repo`, `--once`, `--interval`, `--live`, `--env-file`, `--vibe-report`, `--asi-catalog` | Single repo scan/poll; creates mock or live review DB; live loads controller env and spend ledger; JSON stdout; catches errors by type; no automatic paid retry |
| `scripts/run_repo_steward_fleet.py` | `--config`, `--once`, `--env-file` | Explicit per-repo mode/interval; shares single-repo stores; loads live credentials if any entry live; JSON stdout; parked |
| `scripts/view_repo_steward.py` | `--db`, `--port` | Opens/creates store and serves loopback HTML; default live review DB |
| `scripts/triage_repo_steward.py` | `--repo`, `--sha`, `--finding`, `--decision`, `--note`, `--db` | Validates full lowercase SHA and selected finding; writes confirmed/dismissed decision; JSON stdout |

There is no `descend doctor`, act CLI, corpus/scoring CLI, offline end-to-end
demo, or static export builder in this baseline. These are required work,
not existing capabilities. The directive's reference to an existing doctor
does not match this checkout.

## Store schema and state files

| Store / table | Fields and authority |
|---|---|
| `steward-mock-v2.sqlite`, `steward-reviews-v2.sqlite`: `reviews` | `(repo, sha)` primary key; `created_at`, `status`, JSON `payload`. Atomic insert claims once; cached responses can be revalidated without a provider call |
| Same: `decisions` | `(repo, sha, finding_index)` primary key; `decision`, `note`, `decided_at`. Human triage is not execution approval |
| `cloud-spend.sqlite`: `policy` | `cap`, `halted`; cumulative ceiling cannot be raised by constructor |
| Same: `calls` | `id`, `run_id`, `reserved`, nullable `charged`, `provider_id`; ambiguous requests retain holds; observed overrun halts further reservations |

Default files live under ignored `controller_state/`; custom DB paths are
accepted by view/triage. SQLite may create journals/sidecars. Reviews retain
paths, cited source, raw model content and provider IDs: local state is private,
not a ready-to-publish dataset. Fleet reads its explicit config path; optional
reports/catalogs are user-selected files. `.env` is controller-only and ignored.

## Shared dependencies and other trust crossings

| Dependency | Steward-relevant interface and IO |
|---|---|
| `controller/environment.py` | `parse_environment`, `load_controller_environment`, `main`; reads literal allowlisted assignments, updates only process env; existing env takes precedence; syntax errors omit values |
| `controller/spend.py` | `SpendLedger.__init__`, `reserve`, `settle`, `summary`; `SpendExhausted`; SQLite operations as above |
| `controller/token_factory.py` | `chat_request`, `INFERENCE_BASE_URL`; offline request construction. Fine-tuning/LoRA helpers are not called by Steward |
| `controller/inference.py` | Imports `PRICE_POLICY`, `SUPER_MODEL_ID`; Steward does not call `TokenFactoryInference.complete`; separate DM0 provider call is outside this inventory's product scope |
| OpenAI/httpx | Controller network client; retries disabled, redirects disabled, environment proxies disabled; request deadline 60 seconds |
| `sandbox/hard_isolation.py` | Future reuse candidate only; current Steward does not invoke it. Public `isolation_available`, `build_agent_root`, `run_in_hard_isolation`, `probe_script`, `mock_tool_proxy_echo`; private permission preparation and pipe process transport |

Existing isolation writes a scratch script, root tree and shell wrapper; bind
mounts system runtime directories read-only and a writable workspace, creates
tmpfs/proc mounts, drops to nobody, isolates network/PIDs, and has memory/time
limits. The non-tool path captures unbounded output; no explicit act-specific
CPU/file-count/test-tamper policy exists. It must not be presented as a finished
WP3 worker. No runtime design was changed in this inventory phase.

## Existing test mapping (not rerun this session)

| Surface | Existing test file |
|---|---|
| Watch/store/claim/persistence/sensitive content | `tests/test_repo_steward.py` |
| Parsing/citation correction/schema | `tests/test_steward_findings.py` |
| HTML escaping/decision rendering | `tests/test_steward_dashboard.py` |
| Fleet configuration | `tests/test_steward_fleet.py` |
| Vibe/ASI identity | `tests/test_steward_vibe_context.py` |

Mapping is not exhaustive adversarial coverage. New baseline execution,
coverage of all inventory rows, helper-execution regression tests, and the WP4
attack matrix remain pending. References are read-only codebooks; no source,
held-out answers, or private evaluator data were copied into fixtures.
