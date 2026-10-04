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

Published clean-checkout verification is the next release check and will be recorded here after publication.

Phase status remains **PHASE 1.6 PARTIAL**. The five priority repairs are covered by tests. Remaining prerequisites include actual A/B length matching, complete dependency locking, a truncation anchor, real artifact/code identities and measured token accounting. Documentation/API inspection does not establish live account compatibility. No paid provider calls have been run.
