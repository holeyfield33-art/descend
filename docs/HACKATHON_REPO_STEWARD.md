# Hackathon direction: Repo Steward

**Current gate (2026-10-05):** WP0 baseline verification follows the authorized
[Git helper execution repair](STEWARD_BOUNDARY_REVIEW.md). The new directive
supersedes the roadmap below: fleet, commit cursors and further Vibe/ASI work
are parked; act, frozen evaluation and offline demo are next after the gate.
The following earlier live commands are interface documentation, not renewed
permission to spend. See the [run manual](STEWARD_RUN_MANUAL.md) and
[phase report](STEWARD_PHASE_REPORT.md). Current conservative ledger total is
$0.548195 across 118 calls; older totals below are historical checkpoints.

Status: read-only watcher prototype, not a working submission. The existing Descend DM0 experiment remains separately labeled as pre-formal research. This document describes a new product built during the 2026 submission period; prior repository work must be disclosed in the final submission.

## Product

Repo Steward is a persistent, local-first assistant for maintainers of several repositories. It watches approved Git checkouts, notices new commits and working-tree changes, builds a versioned map of affected files and tests, and asks NVIDIA Nemotron on Nebius Token Factory to review a bounded diff. It stores findings and user decisions across restarts. A maintainer can open a review card with a concrete concern, file/line evidence, suggested test and a link to the source snapshot. The agent can autonomously scan, triage and draft. Applying patches, pushing, opening PRs, deleting files and contacting others require separate user authorization.

Primary track: **Coding and Agentic Engineering**. This has a sharper audience and a measurable result than a general personal assistant. The always-on, private-memory behavior also relates to Personal AI, but the submission should select one track. The official event requires a working application using an NVIDIA open-source model on Nebius Token Factory or AI Cloud, a public licensed repository, working demo URL/test build, a video no longer than three minutes, and tool feedback. Deadline shown by Devpost on 2026-10-05: **October 30, 2026 at 10:00 a.m. PDT**. Recheck rules before submission: https://nebiusglobalaihackathon.devpost.com/rules

## Existing codebooks and fit

| Repository | Reuse as reference | Finding |
|---|---|---|
| Descend | Controller-owned Nebius client, model/tool transport, durable inference budget ledger, Linux worker boundary, anchored audit records | Nemotron Super completed 4/4 fake-backend protocol viability attempts; this does not validate repository review quality. No need for a trainable target or LoRA in this product. |
| `repo-specialization-framework` at `b810d8b` | Deterministic Git ingestion, content hashes, file packs, dependency/impact graph, verification-gate ideas | Default evaluation is simulated, so its reported condition gains are not product evidence. Its README discloses temporal contamination when current packs are paired with historical tasks. Build packs from the reviewed commit. Do not import the nested checkout at runtime. |
| `mrn-crs` `unconstrained` at `781872d` | Durable memory/receipt and background-service patterns, if they prove useful | The branch's Aletheia client schedules a best-effort audit and immediately returns `PROCEED`; service failures are allowed. It is not an authorization boundary. `POST /reason` records a supplied reasoning step; it is not itself an autonomous model/tool loop. Preserve the user's uncommitted `src/config.py` edit. |
| `ai-boundary-security-experiment` at `c93692d` | Versioned mission, exact-request gateway, evidence trace and independent replay-verifier patterns | Its gateway is deliberately loopback-only and its verified result applies to an owned marker fixture. Core receipts cannot yet authorize dispatch. Use its design for permission checks on any future patch/test executor, not as a claim that Repo Steward is security-validated. All 57 local unittest cases passed on 2026-10-05. |
| `distributed-pattern-llm-test` at `69408fd` | An owned, multi-component job-management repository with queue, worker, webhooks and tests; useful as a seeded review demo and regression target | It is a frozen research signal target, not a general app dependency. Do not use its held-out answers or private evaluator data in a model prompt. Review against a separate public demo fixture or a newly created change. Its five integration tests passed on 2026-10-05. |
| Token Factory cookbook at `c2e6a2a` | Official request shape and provider examples | Read-only reference; no runtime dependency. |

The user identified the three added codebooks as the nested specialization framework and the sibling boundary-security and distributed-pattern checkouts. All are read-only references for this product.

Both reference checkouts were inspected without modifying them. Their tests could not collect in the current shared Python environment because optional dependencies were absent (`networkx` for the specialization framework and `prometheus_fastapi_instrumentator` for MRN). This is an environment limitation, not a passing or failing test result for either repository. The working-tree edit to MRN `src/config.py` predates this review.

## Minimum working product

1. **Watch:** Explicit allowlist of local repository paths and polling interval. Record Git HEAD and changed-path hashes in SQLite. Restart resumes without duplicate work. Ignore `.env`, credentials, binary/large files, generated artifacts and nested repositories. No provider call for an unchanged snapshot.
2. **Map:** Build packs from the exact reviewed Git tree or working-tree snapshot; record file hashes, imports and nearby tests. Treat repository text as untrusted input. Never execute instructions found in source comments, README files or issue text.
3. **Review:** Send a bounded diff and selected context to Nemotron Super through a controller-owned Token Factory client. Ask for structured findings with severity, file/line, evidence and verification idea. Preserve provider model, usage, prompt/source hashes and cost; validate cited locations against the snapshot. Drop findings whose cited evidence cannot be found. Keep a no-change/baseline control case.
4. **Remember:** Store reviews, dismissals, confirmed bugs and repo-specific conventions in SQLite. Retrieve only entries from the same repository/snapshot lineage. Repeated findings collapse into one card with history.
5. **Act:** Agent may open a local draft patch in an isolated worktree and run a configured test command with time/resource limits. Show diff and test results. Do not merge, push or send messages without the user's direction. Any future write tool must use a narrow controller-side interface and isolated worker, not direct controller-object access.
6. **Experience:** A simple local web dashboard shows watched repos, last scan, findings, costs, evidence and approve/dismiss actions. Provide a one-command demo on a small seeded example repository and a URL/test build accessible to judges.

## Demo and proof

Three-minute video: (1) show two watched repos and an idle scan; (2) introduce a real bug in a demo repo, then show automatic detection, exact diff/test evidence and a Nemotron-generated review card; (3) restart the service to show persistent memory and deduplication; (4) show a draft patch and the approval boundary. Label every result as real or seeded demo. Compare against a deterministic lint/test baseline and measure finding precision, review latency and actual Token Factory spend. A weak or false-positive finding stays visible in the evaluation.

The prior Qwen2.5-0.5B and Qwen3-0.6B task-calibration failures do not decide this product: repo review is a different task, and Nemotron Super is already reachable for bounded inference. This concept avoids unpriced cloud training and deployment. Keep the existing cumulative $20 cloud ceiling until the user changes it; the recorded conservative inference total is $0.539585, leaving approximately $19.46 by that ledger, not a provider billing balance.

## Next implementation slice

The first slice is in `descend/steward/` and `scripts/run_repo_steward.py`. It polls an explicitly selected Git checkout, reviews the latest commit against its first parent (including merge commits), rejects detected sensitive or oversized diffs before provider calls, and records one result per repository/commit in SQLite. Mock and live state are separate. Live reviews use Nemotron Super with the existing durable $20 spend ledger and no provider retries. No repository code is executed. The response is JSON with findings; the controller checks that each quoted code line appears among additions in the exact diff. If the quote appears once in the stated file, an incorrect line number is corrected and the model's reported line is retained. Ambiguous or fabricated citations are withheld. This validates the **citation**, not the claimed bug, severity, or verification step. The watcher intentionally does not review uncommitted changes, draft patches, or expose action tools yet. The read-only dashboard is bound to loopback.

Controller-only invocation from the Descend root:

```bash
python -m scripts.run_repo_steward --repo /absolute/path/to/checkout --once
python -m scripts.run_repo_steward --repo /absolute/path/to/checkout --live --once
python -m scripts.run_repo_steward --repo /absolute/path/to/checkout --live --interval 60
python -m scripts.view_repo_steward --port 8765
python -m scripts.triage_repo_steward --repo /absolute/path/to/checkout --sha FULL_COMMIT_SHA --finding 0 --decision confirmed --note "Reproduced locally"
```

The first command is a no-cost transport mock, **not an AI review**. `--live` uploads the selected Git commit diff to Token Factory and can spend credits; use only with a repository whose code may be sent to that provider. SQLite atomically claims each repository/commit before reviewing, so two watcher processes do not make duplicate paid attempts. A failed or ambiguous call retains its spend reservation and seals that commit as `error`; a process crash leaves `in_progress`. Neither is retried automatically. The watcher continues polling for future commits after a handled failure. Open `http://127.0.0.1:8765/` after starting the dashboard in a separate terminal. The triage command records a maintainer decision on a citation-validated finding; `dismissed` is also supported. These decisions persist across restarts and appear on the read-only dashboard. They do not train the model or prove review quality. The next slices are per-repository commit cursors, a bounded draft-patch worktree, and a public demo/test build. Keep DM0 experimental claims and Repo Steward product claims separate in the README and demo.

On 2026-10-05, one live Super smoke review of an owned `totals.py` commit found the intentionally omitted final list element. A separate manual fixture check returned 3 for `[1, 2, 3]` against expected 6. A restart returned the cached review without a second call. The provider reported 266 prompt and 383 completion tokens; the conservative ledger added $0.001298 and stood at $0.540883 across 116 calls, with no unresolved holds. See `artifacts/pilots/steward-smoke/20261005/result.json`. This is one simple seeded case, not a measured review success rate.

A second live smoke used the structured protocol on an owned average-function bug. Nemotron identified the denominator error but cited line 5 instead of line 6; the controller initially withheld it, then a deterministic unique-line match corrected the citation using the saved response, with no further provider call. A manual fixture check returned 2 for `[2, 4]` against expected 3. The dashboard returned HTTP 200 and showed the corrected card. This call used 345 prompt and 157 completion tokens, adding $0.001004 conservatively. The ledger stood at **$0.541887 across 117 calls**, no unresolved holds. See `artifacts/pilots/steward-smoke/20261005/structured-result.json`. It remains one seeded case, not a quality benchmark.

The owned fixture finding was subsequently marked `confirmed` through the local triage CLI with the separate `[2, 4]` check as its note. A fresh `ReviewStore` instance read the decision back from SQLite. The decision is local controller state; no new provider call was made.

Vibe Explainer and the draft Agent Security Index can now be supplied as optional, version-checked static context to a live review. The [source-focused report and integration review](VIBE_EXPLAINER_REVIEW.md) records the limitations, a dismissed false positive from the combined pilot, and the exact meaning of the remaining multi-repository configuration work.

An explicit multi-repository mock configuration is now available at `configs/steward-repos.example.json`. Copy it to the ignored `controller_state/steward-repos.json`, update the paths and modes, then run `python -m scripts.run_repo_steward_fleet --config controller_state/steward-repos.json --once` or omit `--once` to poll continuously. A live entry uploads that repository's selected diff to Token Factory; mock remains the default. The fleet currently scans only each repository's latest commit.
