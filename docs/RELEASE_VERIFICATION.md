# Release verification

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

Current cloud accounting is $0.533707 conservatively across 113 calls, against the authorized $20 cap, with no unresolved calls. Real training/deployment and formal claim runs remain gated. The successful Super pilot had a one-token A/B provider-wrapper difference despite matching input-content counts; it does not establish formal length matching or H1.
