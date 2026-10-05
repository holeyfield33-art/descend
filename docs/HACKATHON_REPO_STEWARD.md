# Hackathon direction: Repo Steward

Status: scoped product direction, not a working submission. The existing Descend DM0 experiment remains separately labeled as pre-formal research. This document describes a new product built during the 2026 submission period; prior repository work must be disclosed in the final submission.

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

Create a separate app package in Descend or a new standalone repository after the remaining reference folders are identified. First ship a read-only watch → snapshot → Nemotron review → SQLite finding loop with a deterministic mock provider for tests. Then add a minimal UI and a real bounded provider smoke test. Keep DM0 experimental claims and the Repo Steward product claims separate in the README and demo.
