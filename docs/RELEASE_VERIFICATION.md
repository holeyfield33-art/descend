# Release verification

**2026-10-06 live measurement:** user-approved frozen plan completed all
104 review calls and one proposal. The proposal failed syntax validation and
halted acts; no live generated code executed and no patch applied. All responses,
usage/IDs, errors, false positives and misses are retained. Additional accounted
spend $0.065495; cumulative $0.613690, zero holds. New public exporter tests:
3 Windows passes, including HTML escaping and pre-write secret/identity refusal.
See [live results](STEWARD_LIVE_RESULTS.md) and the updated run manual.

**Final offline readiness at `46428f9`:** fresh public Linux clone 202 passed,
zero skips; fresh public Windows clone 158 passed, 44 explicit skips. Both source
statuses clean. Locked environments reused. Final frozen-plan hashes verified
on both hosts; actual Linux worker doctor passed. No paid calls were made.

**2026-10-05 Steward WP4/WP5:** 197 Linux passes, zero skips; 155 Windows
passes, 42 explicit skips. The doctor ran the actual filtered worker probe.
All 24 known fixture fixes reverified. The owned offline demo demonstrated
PATCH_VERIFIED, unchanged checkout, restart deduplication and zero provider calls.
These are mock/oracle results. Independent red-team and live comparative model
evaluation remain pending. See [phase evidence](STEWARD_PHASE_REPORT.md).

**2026-10-05 Steward WP0:** the authorized Git helper repair passes the full
Linux suite (125 passed, no skips) and Windows suite (100 passed, 25 skips;
Linux worker unavailable and one symlink-privilege skip). Doctor records both
environments and reports act readiness false. Fresh-clone verification follows
publication and passed at `3af3ed9`: Linux 125 passed; Windows 100 passed,
25 skipped, matching baseline. See the [phase report](STEWARD_PHASE_REPORT.md) for complete
output, intermediate failures and limitations. Older counts below are historical.

This update publishes the recovered source tree, integrated fake-worker boundary, protocol repairs, offline Token Factory request preparation and current documentation. The cookbook remains a separate read-only reference checkout at `c2e6a2a4651ba8fd126365d7bbcd2b5621acb040`; it is not a runtime dependency.

The historical recovery and repair reports preserve the counts measured at their respective milestones.

## Workspace checks

| Check | Result |
|---|---|
| Ubuntu WSL / Python 3.14.4, trusted root launcher | 84 collected, 84 passed, no skips/failures/errors |
| Native Windows / Python 3.14.6 | 84 collected, 61 passed, 23 skipped, no failures/errors |
| Cookbook checkout | Clean and unchanged at the pinned commit |
| Paid provider requests | None; contract tests are offline |

## Published clean-checkout checks

A fresh clone from GitHub at `4b8ddc47166ad7005a43d81cbed82139ee90ffe6` was installed with `pip install -e ".[dev]"` in new Windows and Linux virtual environments. The source tree contains 91 tracked files, including all restored manifest implementations.

| Check | Result |
|---|---|
| Fresh Linux checkout | 84 collected, 84 passed, no skips/failures/errors |
| Fresh Windows checkout | 84 collected, 61 passed, 23 skipped, no failures/errors |
| Fake A and B, seed 42, Linux isolation | Both completed; each registry chain verified with 11 events |
| Checkout after verification | Clean; generated artifacts ignored |
| Cookbook runtime dependency | None; the reference checkout was not installed or executed |

The fake runs validate plumbing and synthetic scoring, not Nemotron inference or training quality. Subsequent release-documentation changes do not alter the tested implementation.

The first publication, `7ff3c769426bbeb04d0547ad6aa0172acd4d9726`, failed fresh-clone collection with nine errors on both platforms: three restored manifest implementation files were still ignored by the inherited unanchored `MANIFEST` rule under Windows's case-insensitive matching. Workspace tests could see those files, which is why they passed. The release correction anchors that generated-file rule to `/MANIFEST` and explicitly publishes `descend/manifest/build.py`, `neutral.py` and `schema.py`. No implementation was invented to mask the missing files.

The checks above describe the recovery release. The current implementation additionally provides paired input matching, exact runtime dependency versions, truncation anchors, actual local artifact/source identities and measured provider usage. Real Nano/Super inference pilots have run with fake training/scoring. Real target training, deployment and formal DM0 claims remain gated; see [Phase 2 status](PHASE2_STATUS.md).

At implementation commit `b08b25b`, Linux collected and passed all **101 tests**; native Windows passed **77**, with **24 Linux-only skips**. The live-budget schema test verifies exhaustion and commitment ordering without relaxing enforcement. An independent artifact audit checks all saved attempt records, anchored registries, transcripts, candidate bytes, frozen predictions and available runtime snapshots. The first failed batch has Git/source hashes but no byte-for-byte source snapshot; the audit reports this limitation explicitly.

## Current published release verification

A fresh GitHub clone at `54edc0513a48cb76fa644f0fd888bfb45bf40b55` was installed in a new Linux virtual environment using `requirements-lock.txt`, followed by `pip install --no-deps -e .`. The lock pins runtime/test dependencies; isolated build-tool dependencies are not pinned by it.

| Check | Result |
|---|---|
| Fresh Linux clone | 102 passed, no skips or failures |
| Current native Windows checkout | 78 passed, 24 Linux-only skips |
| Archived pilot audit in fresh clone | All five batches, 20 attempts verified |
| Latest real Super/fake-target viability | 4/4 completed; GO |
| Python syntax and Markdown control characters | Passed |
| Known current API credential in reachable Git objects | Absent from all 609 scanned objects |
| Cookbook sibling | Unchanged; no runtime dependency |
| Clean clone after verification | Clean |

That fresh-clone row records its historical checkout. On the current checkout, native Windows ran 106 collected tests: 82 passed and 24 Linux-only tests skipped. A Linux rerun could not start because WSL instance creation timed out (`0x800705b4`); the prior Linux result was 105 passed before the latest documentation/calibration artifacts. Current conservative cloud accounting is $0.539585 across 115 calls, against the authorized $20 cap, with no unresolved calls. Real training/deployment and formal claim runs remain gated. The successful Super pilot had a one-token A/B provider-wrapper difference despite matching input-content counts; it does not establish formal length matching or H1.

The separate Repo Steward prototype added two watcher tests. On 2026-10-05, native Windows collected 108 tests: **84 passed, 24 Linux-only skipped**. The owned live-review smoke made one Super call and restart deduplication made none; conservative accounting is now **$0.540883 across 116 calls**, no unresolved holds. This is product-prototype evidence, not DM0 formal evidence or a complete hackathon submission. See [Repo Steward direction](HACKATHON_REPO_STEWARD.md).

A subsequent structured-review pilot made one more Super call, then corrected the model's off-by-one citation using a unique exact added-line match without a second call. The loopback dashboard served the corrected card with HTTP 200. Conservative accounting is **$0.541887 across 117 calls**, no unresolved holds. The structured output does not establish bug-finding precision; its citation validator only proves that displayed evidence came from the reviewed diff.

After the structured validator and dashboard changes, native Windows collected **114 tests: 90 passed, 24 Linux-only skipped**. The new tests cover valid and fabricated citations, unique-line correction, ambiguity, malformed responses and HTML escaping.

After the atomic review-claim change, native Windows collected **116 tests: 92 passed, 24 Linux-only skipped**. The added cases prove that a second watcher sees the in-progress claim instead of calling the provider and that a failed call is not retried automatically. The prior 114-test count remains a historical checkpoint.

After persistent maintainer triage was added, native Windows collected **117 tests: 93 passed, 24 Linux-only skipped**. The decision test checks that a confirmed finding survives reopening the SQLite store and that a nonexistent finding cannot be triaged.

An optional Vibe/ASI context adapter subsequently passed its focused validation test and a bounded live combined pilot. The private source-focused Vibe report is pinned to Descend commit `d9fc489`, with a complete inventory and matching ASI catalog hash; [the analyst review](VIBE_EXPLAINER_REVIEW.md) separates static leads from code-verified findings. The pilot's single Nemotron claim was citation-valid but dismissed after code review. Conservative ledger accounting is **$0.548195 across 118 calls**, no unresolved holds.

After the explicit multi-repository fleet configuration and two config tests, native Windows collected **120 tests: 96 passed, 24 Linux-only skipped**. A no-cost fleet pass scanned Descend, Vibe Explainer and Agent Security Index from one private config; only Descend's latest commit contained code in that pass. No new provider calls were made by the fleet test.
