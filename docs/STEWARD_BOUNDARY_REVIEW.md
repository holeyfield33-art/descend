# Steward boundary review: Git helper execution

Status: OPEN; static source review, 2026-10-05, source `b59a470231ec99d33ba297204dec9d4844c563ee`.
No exploit was executed. WP0 is paused at the directive's stop-and-ask gate.

## Finding

`descend/steward/watch.py::_git` starts Git on the controller host with the
controller's inherited environment. `commit_snapshot` uses `git diff --patch
--no-ext-diff` for ordinary commits and `git show --no-ext-diff` for root commits.
Neither path supplies `--no-textconv`.

Git distinguishes external diff drivers from text-conversion filters.
Its [official diff documentation](https://git-scm.com/docs/git-diff#Documentation/git-diff.txt---textconv)
documents the separate switch and the default enabling of text conversion for
porcelain diff/log operations. Disabling external diff drivers alone does not
establish a no-helper-execution boundary.

A file attribute selecting a diff driver, together with an effective Git
configuration defining that driver's textconv command, can cause a scan to
launch a helper on the controller. The helper inherits controller permissions
and environment. This is before the sensitive-content and diff-size gates.
Both mock and live scans share this code path. The model need not be involved.
Tracked `.gitattributes` alone does not define an arbitrary executable command;
the configured helper is an explicit precondition. This is not evidence that
any existing watched checkout is malicious or that a credential was exposed.

## Proposed repair for human review

1. Resolve the Git executable to an absolute path. Route every Steward Git
   operation through one controller-owned invocation policy.
2. Disable textconv and external diff helpers on every diff-producing path;
   use explicit nonrecursive submodule handling. Review other implicit execution
   mechanisms (including fsmonitor), Git environment overrides, configuration
   includes, and inherited credentials before claiming the reader is inert.
3. Give Git a minimal explicit environment with no provider credentials.
   Ensure errors never echo environment values or private source.
4. Add regression cases for root and non-root commits and mock/live entry
   points. Use an owned harmless marker helper inside the Linux test boundary;
   verify that the proposed reader never invokes it. Do not execute a hostile
   fixture on the user's controller host.
5. Re-run the full inventory coverage, Windows protocol and Linux suites, then
   fresh-clone verification. Retain the original tests unchanged.

The repair is proposed, not implemented. It preserves read-only review and the
future export-only act boundary. No sandbox escape or secret access was tested.

## Why work stopped

Section 8 of the user-supplied Repo Steward directive requires stopping and
asking upon finding a route to a secret, network, or real-checkout modification:
“stop, document, do not quietly fix and move on.” A controller-side helper runs
with those capabilities. This is the required escalation, not a new approval
policy invented by the implementation agent.
