# Repo Steward: gap register and specialization-framework review

Assessment date: 2026-10-06. This is the complete **known-gap inventory for the
proposed hackathon scope**, not a claim that a static review discovers every
defect. No product changes, training, paid calls, deployment, independent
red-team clearance or new evaluation are represented by this document.

## Recommendation

Keep Repo Steward as the submission: a persistent repository reviewer that
turns a suspicious change into cited evidence, an isolated reproduction and an
exportable patch within an explicitly supported scope. Recommend the Coding
and Agentic Engineering track. Make the successful, live, bounded workflow the
center of the demo; show unsupported actions and unsuccessful proposals honestly.

Use repo-specialization-framework (RSEF) as a read-only design reference for
commit-bound file packs and dependency context. Do not merge its research runner,
verification gate or training stack into Steward. First measure whether better
context improves the existing Nemotron reviewer. Fine-tuning is an optional
later experiment, not a prerequisite for this submission.

The evidence does not establish that model size caused the current failures.
Both models found 15/16 seeded bugs by location scoring; output reliability,
abstention, task representativeness and the proposal contract are immediate
problems. More parameters or a LoRA adapter might help, but neither is a measured
fix. Super is the provisional development default because it produced fewer
false positives in this run, not because it is generally proven superior.

## Review basis and traceability

- Descend inspected at `c1e6d0fa6e810aa45cc0daaa855826746baeab18`.
- RSEF local clean checkout and remote HEAD both identify
  `b810d8b397d2858a2693a8232599a5982dd25a19`; remote checked with `git ls-remote`.
  [Pinned reference repository](https://github.com/holeyfield33-art/repo-specialization-framework/tree/b810d8b397d2858a2693a8232599a5982dd25a19).
- Read RSEF ingestion, packs, graph, task generation, prompting, evaluation,
  runner, relevant training/provenance logic, tests, CI and saved results.
  This was a source/artifact review; its test suite and GPU training were not run.
  The RSEF checkout was not modified. Repository comments and README claims
  were treated as evidence to inspect, not instructions to execute.
- Steward sources inspected: watcher/store, reviewer, proposal proxy, Vibe/ASI
  adapter, dashboard and launchers; existing worker/attack/release evidence
  reviewed through the current reports. This is not a fresh independent audit.
- Existing [live evidence](STEWARD_LIVE_RESULTS.md),
  [attack matrix](STEWARD_ATTACK_MATRIX.md),
  [phase report](STEWARD_PHASE_REPORT.md),
  [run manual](STEWARD_RUN_MANUAL.md) and
  [extraction plan](STEWARD_EXTRACTION_PLAN.md) remain authoritative for completed work.
- [Official rules](https://nebiusglobalaihackathon.devpost.com/rules), checked
  2026-10-06, list the deadline as **October 30, 2026, 10:00 a.m. PDT**.
  A runtime Token Factory inference call qualifies as running on the required
  platform; a Nebius-hosted application is not the only route. The required
  deliverables include a working demo/test-build URL, public licensed source,
  setup instructions, track, description, public YouTube demonstration under
  three minutes, platform feedback and disclosure of significant prior-project
  updates. Account eligibility, registration and actual submission were not verified.

## What already exists

These are foundations to preserve, not work to recreate: controller-side Nebius
Nemotron inference, a cumulative spend ledger, atomic review/action claims,
citation validation, a loopback dashboard and persistent human triage; a narrow
Linux namespace/chroot/seccomp worker; test-tamper checks and export-only patches;
an offline end-to-end demo; a frozen original corpus; recorded Super/Nano raw
responses, costs and failures; static public bundles, license and operating docs.

Recorded validation is 205 Linux passes and 161 Windows passes with 44 explicit
skips at the published test checkpoint, followed by targeted cross-platform
export verification. This review did not rerun those checks. Live evaluation
made 105 calls for $0.065495 conservative additional accounting, cumulative
$0.613690. This is not a provider receipt or verified credit balance.

## RSEF findings and reuse decisions

Source references below are relative to the pinned RSEF checkout above. Static
findings describe the inspected code; they are not claims of an exploited
Steward vulnerability. Only fix the RSEF issues needed by a selected adaptation,
unless a separate research-harness repair is chosen.

| ID | Observed issue and evidence | Consequence / required treatment |
|---|---|---|
| R01 | `src/evaluation.py:78–118`, `deterministic_verify`, sets `source_ok = True`; it never compares actual source bytes to the expected source hash. The caller passes a pack hash and a source hash, which are different identities. | Do not reuse this gate. Verify distinct source/pack/graph identities against actual bytes and a trusted commit manifest. A deliberately stale or changed artifact must fail. |
| R02 | `scripts/run_experiment.py:232–243` supplies literal test names, `patch_clean=True`, `static_ok=True` and zero violations; saved `results/verification_gate.json` says PASS. | This is no proof of execution or patch correctness. Replace with controller-owned execution records, or mark checks NOT_RUN; retain Steward's real worker authority. |
| R03 | HEAD-state packs are used for older tasks; README and `train_real.check_temporal_integrity` acknowledge the contamination and warn rather than prohibit it. | For any training/history experiment, materialize the correct task-time snapshot and enforce an information cutoff. Freeze manifests before evaluation. |
| R04 | `history_tasks.generate_tasks_from_history` derives impact answers from the same graph supplied to condition D and tests from filename heuristics. Code-review/cross-file explanation tasks are excluded by `prompting.is_scoreable`. | Graph-answer reproduction is not independent bug-finding or reasoning evidence. Use independently validated behavior and test-impact labels; report excluded tasks. |
| R05 | `real_model_response` calls any expected/predicted path intersection success. `evaluate_condition` uses path recall as `test_pass_rate`, assigns zero security regressions and derives unnecessary edits without executing edits. Successful raw completions become a short path-count summary. | Do not adopt these headline metrics. Track precision, recall, exact sets, abstention, executed tests and unmeasured values separately; preserve complete raw responses and inputs. |
| R06 | `results/summary.json` is simulated. `_simulate_model_response` hardcodes A/B/C/D base rates and uses Python's process-dependent `hash()` seed. | No empirical adaptation gain is demonstrated by saved results. Keep simulation visibly separate; use stable digests for reproducible simulation if retained. |
| R07 | `ingestion.py` reads the working tree with `os.walk`/`read_bytes`, before its per-file content cap, then records Git HEAD. No clean-tree or tracked-blob identity check; supported-extension symlinks/untracked files can be read. GitPython calls do not use Steward's hardened wrapper. | Never point this unrestricted ingestion directly at a private workspace as a Steward tool. Use bounded exact-commit Git blobs, explicit scope, symlink refusal, path/secret checks and the existing Git boundary. |
| R08 | JS/TS regex symbol extraction is the implemented parser. Relative imports with `..` are not lexically normalized against manifest paths; extension candidates are JS-focused. Name matches become low-confidence CALLS edges. | Build a small Python AST/import adapter for the initial product scope; preserve uncertainty. Do not present name matching as proven call relationships or promise all supported diff languages have semantic graphs. |
| R09 | `DependencyGraph` uses `nx.DiGraph`: later edges overwrite the type for the same pair while the separate edge list retains all types. Neighborhood uncertainty does not propagate `self.uncertainty`; when seeds exceed `max_nodes`, seed preservation can exceed the cap. | Preserve multiple typed edges, propagate unresolved imports and enforce a hard selection/output budget. Deterministic bounded fixtures should cover each case. |
| R10 | Pack filenames flatten `/` and `\\` to `__`, so `a/b.py` and `a__b.py` collide. `prompting.load_pack` loads JSON without validating recorded hashes. Pack hashes omit later semantic fields/version; graph identity is not a digest of complete graph semantics/extractor version. | Use collision-free content-addressed storage; hash the whole schema/versioned payload; validate all identities and paths before prompt assembly. A hash identifies content, not its truth or authority. |
| R11 | `ingestion.py` makes one change family per commit; synthetic tasks share `synthetic-validated` across splits. Audit checks metadata and partial answer strings, not every actual context token; the runner reports contamination after evaluation. | Do not claim deduplicated change-family isolation from these names. Group related fixes/backports, audit actual prompts and artifacts before training/eval, and keep evaluator labels outside tool context. |
| R12 | A is flat source concatenation, not an implemented retrieval system; B/C can receive up to 12 source blocks of 1,200 characters plus metadata versus A's 6,000-character source cap. Default real models are Qwen/SmolLM, not the current NVIDIA/Nebius path. | Build token-matched diff/flat-context/pack/graph ablations using the same Nemotron model and retrieval candidate set. Do not attribute context-volume or retrieval differences to tuning. |
| R13 | No tracked LICENSE was found in the inspected RSEF commit. `requirements.txt` is broad/unlocked; core/ML CI jobs exist but installs are unpinned. | Before copying implementation, record ownership/attribution and supply an appropriate license. Adapt minimal owned code into Steward with pinned minimal dependencies; do not import the entire training environment. CI existence alone is not proof that a current run passed. |

Useful concepts to adapt: file and commit identities, typed dependency evidence,
explicit uncertainty, provenance on semantic summaries, and controlled context
comparisons. Training telemetry and adapter provenance are useful only if a
later, separately evaluated training experiment is justified.

## Complete known-gap register

**P0** blocks the recommended credible submission or one of its central claims.
**P1** should follow for a useful persistent reviewer and stronger evidence.
**P2** is conditional/stretch work, not necessary to enter. Status is OPEN unless
marked PARTIAL or UNVERIFIED. Completion criteria below are proposed gates for
future work, not retroactive changes to the frozen v4 evaluation.

### Model behavior and coherent product

| ID / priority | Gap and evidence | Completion criterion |
|---|---|---|
| G01 / P0 | **PARTIAL: reliable review output.** Super had 7/32 schema failures, including six model-content pseudo-errors; these were not SDK timeouts. | Version the output contract, preserve raw content and finish reasons, check supported structured-output API behavior against official examples, and test malformed/empty/truncated outputs. Validate on development data, then a fresh frozen set. Never silently convert parse failure to a clean review. |
| G02 / P0 | **Abstention and false-positive control.** Nano flagged all 11 clean/hard-negative cases; citation validity does not establish a bug. | Define a concrete-bug/evidence rubric and explicit insufficient-evidence state. Measure clean alarms, precision and missed bugs on new independently labeled cases. Proposed initial target: at least 90% precision, at most 10% clean alarms and at least 80% bug recall, with sample counts and uncertainty; failure must remain visible. |
| G03 / P0 | **Successful live act evidence.** First proposal failed syntax/schema constraints; 0/1 attempted verified, seven NOT_RUN. | Correct the development-time proposal contract with valid JSON/code examples and exact supported AST/test conventions. Preserve hard validation. Demonstrate a new live proposal whose reproducer fails before and passes after, with original tests intact, worker evidence and exported patch. Do not repair/replay frozen test responses and relabel them successes. |
| G04 / P0 | **One usable review-to-verification workflow.** Persistent watcher and dashboard show review records; live act orchestration lives in an evaluation runner, while the act CLI is offline. | Add a controller-owned path from selected validated finding to bounded proposal, isolated verification and evidence/patch view; retain explicit policy, durable claims and no checkout mutation. A user should complete this without manually assembling internal artifacts. |
| G05 / P0 | **Supported scope versus product promise.** Act supports `app.py::solve(values)` fixtures; review supports more diff extensions and only added-line citations. | Publish and display the exact supported languages, shapes, size limits, deletion-only/cross-file limitations and platform requirements. Demonstrate the narrow scope honestly; expand to one realistic pure-Python module profile only with worker/test protection retained. General repository patching is not a submission requirement. |
| G06 / P1 | **Repository context.** Live benchmark used diff-only review; there is no RSEF pack/graph integration or measured context benefit. | Implement the bounded commit-specific evidence adapter described below. Stale/private/oversize context is rejected. Adopt richer context only if new ablations justify it. |
| G07 / P1 | **PARTIAL: Vibe/ASI operational integration.** Exact-commit report/catalog pinning exists, but refresh is manual; no measured benefit or bounded input-file parsing claim. | Bound report/catalog reads and schemas, automate safe report selection/invalidation, display taxonomy version/provenance, and evaluate diff-only versus added leads. ASI classes remain investigative leads, never permissions or vulnerability proof. |
| G08 / P1 | **Commit coverage.** `commit_snapshot` reads only current HEAD versus its first parent, so polling can miss intermediate commits. | Persist a bounded cursor/queue, define merges, root commits, branch changes and force-push handling, and test restart/backlog without duplicate charges. If deferred, call it latest-commit polling, not complete history monitoring. |
| G09 / P1 | **Always-on operation.** A polling loop exists; supervised startup, heartbeat, stop/pause, health and sustained-operation evidence are absent. | Provide a supported Linux service/run profile, health state, bounded logs and a recorded soak test with restart, provider outage and budget exhaustion. Support Windows review-only operation explicitly. |
| G10 / P1 | **PARTIAL: incident recovery.** Sealed error/in-progress claims correctly prevent duplicate spending, but operator reconciliation is not a complete workflow. | Add read-only inspection and explicit reconciliation of crash/ambiguous requests and unresolved reservations; preserve audit records and never auto-release unknown spend or auto-replay paid calls. Include backup/restore and disk-full behavior. |
| G11 / P1 | **Review identity and fleet fairness.** Cache key is repository path plus SHA, not model/prompt/context/policy version; fleet has basic configuration but lacks fair queueing and per-repo policies. | Store immutable review identities and separate intentional new protocol runs from duplicate claims; normalize repository identity. Test two repositories, moves, policy changes and independent budgets without weakening sealed benchmark claims. |
| G12 / P0 | **PARTIAL: complete user experience.** Loopback review cards and CLI triage exist; act evidence, queue health, errors, supported scope and context provenance are fragmented. | One clear flow shows selected repo/commit, queued/reviewed/abstained/error/skipped states, cited evidence, unverified versus verified status, cost and patch export. Keep operator controls local and authenticated if write endpoints are added. |
| G13 / P0 | **PARTIAL: onboarding.** Manual exists, but controller and privileged Linux worker setup remain specialist tasks. | A new user follows one supported install/start sequence from a fresh environment, runs doctor and offline demo, then sees how to opt into bounded live mode. Report failures and Windows limitations clearly; never require a private codebook checkout. |

### Trust, evaluation and engineering

| ID / priority | Gap and evidence | Completion criterion |
|---|---|---|
| G14 / P1 | **PARTIAL: data minimization and retention.** Current secret checks are heuristic; local reviews retain source/provider records. New context widens exposure. | Define per-repo send/deny scope, exact-commit extraction, pre-send preview/manifest, bounded retention/export and deletion policy. Test credentials in source/context and symlink/untracked exclusions without claiming universal secret detection. |
| G15 / P0 | **PARTIAL: operational spending policy.** Durable $20 ceiling exists, but always-on operation needs workload/per-repo limits and current accounting; standalone planner has historical assumptions. | Use current ledger state for estimates, explicit per-run/repo call/cost caps, no-key offline mode and visible remaining accounting. Reserve before every new call and retain ambiguous holds. Provider billing reconciliation remains separate. |
| G16 / P0 | **Independent security review.** Automated attacks exist; independent handoff remains pending. | A different reviewer follows the handoff on a pinned commit, reports concrete findings and untested areas, and verifies fixes. This source review is not that clearance. Include new context, lifecycle and UI surfaces before release. |
| G17 / P1 | **No measured benefit from codebooks/context.** Neither RSEF nor Vibe/ASI is demonstrated to improve current review quality. | Freeze same-model diff-only, flat retrieved source, structured packs, packs+graph and optional Vibe/ASI comparisons with matched budgets, deterministic selection and all failures retained. Test context and model choice separately. |
| G18 / P0 | **Representative unseen evaluation.** Current small public seeded families are correlated and no longer unseen; they do not establish general repository accuracy. | Build licensed/owned realistic changes with cross-file cases, clean refactors, insufficient-context cases and attacks; group related families, independently validate labels, separate dev/test and freeze before calls. Preserve v4 unchanged. |
| G19 / P0 | **Semantic adjudication.** Current automatic location matching allows weak matches; no independent blind semantic review. | Blindly adjudicate whether each finding identifies a real defect, its evidence and useful next step; retain disagreements. Report schema failures, abstentions, FP/FN, per-category results and confidence intervals, plus attempted and eligible act denominators. |
| G20 / P1 | **Meaningful baselines.** B0/B1 miss all 16 existing test bugs; weak callable-only tests do not measure practical incremental value. | Include realistic existing test/static-check baselines and an equal-budget plain-context reviewer. Run target tests only in the reviewed worker profile. Publish where each method succeeds, fails or is unsupported. |
| G21 / P1 | **PARTIAL: provenance coverage.** Strong existing raw-record/hash exports need extension for retrieved context and later revisions. | Record source commit/blob IDs, extractor/schema versions, context selections and omissions, prompt/model settings, raw outputs, usage and execution identities end-to-end. Keep outcome labels/evaluator diagnostics out of agent context. |
| G22 / P0 | **Continuous verification.** No tracked Descend GitHub workflow was found at this commit; local evidence exists. RSEF has its own CI, which does not cover Steward. | Add locked Windows protocol/export and Linux worker jobs on a runner capable of actual isolation; fail the designated worker gate on missing prerequisites instead of accepting skips. Publish exact release SHA and check logs; CI makes no paid calls. |
| G23 / P1 | **PARTIAL: standalone packaging.** Extraction is planned, not done; user will supply a destination. | When destination exists, extract explicit allowlist, minimal dependencies, license/provenance, docs and CI; validate a fresh clone with no Descend/codebook imports or private state. A focused release within Descend is an acceptable interim submission path. |

### Submission and demonstrated value

| ID / priority | Gap and evidence | Completion criterion |
|---|---|---|
| G24 / P0 | **Judge-accessible working demo/test build.** Local canned demo and static evidence bundles exist; no confirmed hosted application/test-build handoff. | Publish a reproducible working test build or safe hosted demo, clearly distinguish recorded/mock/live views, and verify judge access from a fresh browser/environment. Static results alone are not the whole working product. A public privileged worker is unnecessary. |
| G25 / P0 | **Demo video.** No completed public video verified. | Produce a public YouTube video under three minutes showing the actual product, NVIDIA/Nebius role, live evidence, bounded verification/patch export and an honest failure/limit. Preserve a reproducible demo script. |
| G26 / P0 | **Focused submission narrative and track.** Descend research and Steward product histories coexist. | Lead README/demo/submission with one audience, problem and workflow; recommend Coding and Agentic Engineering. Link research history separately and explain why repository-specific evidence improves the workflow only to the extent measured. |
| G27 / P0 | **PARTIAL: prior-work disclosure.** Existing notes describe reuse but final release needs a precise submission-period change record. | Tie significant new work to dated commits, identify earlier Descend/RSEF/codebook contributions and licenses, and include the required written disclosure with the submitted artifact. |
| G28 / P0 if copying RSEF | **PARTIAL: redistribution provenance.** Descend has MIT; the inspected RSEF commit has no tracked license. | Record copyright/ownership and intended license before publishing copied RSEF code; preserve third-party notices and per-file adaptation provenance. Until then reuse design ideas through original implementation, not a runtime dependency. |
| G29 / P0 | **UNVERIFIED: administrative readiness.** Registration, entrant eligibility, team representative, selected track and completed form are not established by repo files. | User verifies account/eligibility and final required fields; record the actual submitted URL and receipt after submission. Planning does not imply rules acceptance or submission. |
| G30 / P0 | **PARTIAL: platform feedback delivery.** `NEBIUS_FEEDBACK.md` exists; delivery in final submission is unverified. | Include measured useful feedback and provider/model identification in the form/video, with pseudo-error content distinguished from transport failures and accounting distinguished from invoices. |
| G31 / P0 | **PARTIAL: release consistency.** Historical inventory/phase sections intentionally describe older states, which can confuse new users. | Put a current-state navigation page first; label archived plans and never imply the completed v4 plan can be rerun. Freeze release/version, check links/install instructions and preserve evidence hashes. |
| G32 / P1 | **Real-user usefulness.** No recorded maintainer trial establishes less review effort or actionable findings on ordinary work. | Observe at least one external/fresh-user trial on an allowed repo; record setup friction, useful/dismissed findings, time-to-triage and concrete feedback. Do not extrapolate one pilot to a broad productivity claim. |

## Minimal context integration design

1. **Controller chooses the scope.** Given an allowed repository and exact commit,
   obtain bounded tracked blobs through Steward's hardened Git transport. Do not
   import modules, run build hooks, traverse sibling repositories or ingest the
   working directory wholesale. Read parent-state evidence only when identified
   as such. No labels, expected fixes, hidden examples or contamination diagnostics
   enter the context service.
2. **Build immutable evidence.** Use collision-free IDs and a versioned schema
   covering repo/commit/path/blob/source hash, relevant ranges, extractor version,
   imports, candidate tests, typed edges and explicit uncertainty. Verify every
   supplied pack against bytes and its trusted manifest. Semantic summaries carry
   their source references and never become authoritative facts by having a hash.
3. **Select a small context.** Begin with the changed Python module, directly
   related imports/callers and candidate tests, under fixed file, byte, token,
   time and graph-radius caps. Rank deterministically; log omissions/truncation.
   A controller-bounded read-only query such as
   `get_review_context(repo_id, commit, paths)` is sufficient; it grants no shell,
   network, write or execution capability to the model.
4. **Attach Vibe/ASI separately.** Match exact clean commit and catalog digest;
   pass bounded relevant lead IDs with provenance. Their instructions remain
   untrusted data. They prioritize investigation; they cannot authorize an act or
   count as proof of a vulnerability.
5. **Keep execution authority in Steward.** A proposed check/patch goes through
   the existing controller's syntax, scope, spending, replay, worker and
   test-integrity checks. Neither an RSEF PASS nor model text can bypass them.
6. **Measure before enabling by default.** Freeze a new evaluation protocol and
   dataset after development. Compare contexts with the same Nemotron model and
   matched budgets. Preserve unchanged diff-only v4 evidence as history.

## Closure order and decision gates

Effort estimates are planning ranges for focused engineering, not promises of
completion or additional spend authorization. Stages can overlap in documentation
and UI work, but execution/evaluation gates stay ordered.

| Stage | Work / dependencies | Deliverable and exit gate | Rough effort |
|---|---|---|---|
| 1 | G01–G05, G15; use development fixtures only | Reliable versioned review/proposal contract, visible abstention/error states and offline review-to-act workflow. Existing boundary regressions pass. | 2–3 days |
| 2 | G06–G07, G14, G21, R01/R07–R10/R13 as applicable | Minimal Python context adapter with hash/path/budget/injection tests; no RSEF runtime dependency. Can be omitted from first release if it delays the live core workflow. | 2–3 days |
| 3 | G08–G13, G22; scope according to actual product claim | Usable dashboard, cursor/service/recovery behavior and clean-install CI. If cursor/service is deferred, narrow the claim to an explicit local review session. | 2–4 days |
| 4 | G17–G20, G03, G32 after protocol/context freeze | Fresh independent labels, new quantified cost plan, approved live run, complete raw outcomes and blind adjudication. At least one actual verified live patch for the recommended act-demo story; otherwise explicitly submit a review-only product. | 2–3 days plus review availability |
| 5 | G16, G23–G31; final review includes newly added surfaces | Independent findings resolved or scope reduced; working demo/build URL, public code, video, clear evidence and prior-work disclosure; final human submission. | 2–3 days plus reviewer/user availability |

Start the independent review scheduling and demo outline early. Aim to freeze
the product before the final days preceding October 30; preserve time for clean
installation, access checks and recording. A new repository is helpful for a
clear story but is not worth delaying a functioning submission.

The next paid step should be a small, predeclared development contract check
followed by a separately frozen evaluation after fixes, with a new estimate and
approval. The old v4 plan/corpus claims remain sealed. This review authorizes no
new cloud workload and does not assume that unused budget is a new approval.

## Explicitly deferred, not required gaps

- QLoRA/fine-tuning, custom-model deployment and a bigger model: pursue only after
  measuring a remaining failure that data/context/contract fixes do not address.
  RSEF's temporal, metric and gate problems must be repaired before research claims.
- Autonomous checkout application, pushes or merges; general shell access;
  arbitrary repository test execution; broad multi-language patching.
- A public multi-tenant agent service, unrestricted self-improvement, or continuous
  cloud operation. Local persistent operation plus runtime Token Factory calls
  can support the chosen product, provided its actual limits are clear.
- Full repair of the separate RSEF research harness. It is a reference repo;
  its simulated metrics are not part of Steward's claimed results.

Do not expand the project merely to use every available reference repository.
The strongest improvement is a reliable, useful, measured workflow whose
evidence can be traced from a real change to a verified result.
