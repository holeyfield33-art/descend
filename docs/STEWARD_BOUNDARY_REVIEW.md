# Steward boundary review: Git helper execution

Status: repair implemented, 2026-10-05; original source `b59a470231ec99d33ba297204dec9d4844c563ee`.
The user authorized repair and autonomous continuation after the documented
stop. The isolated positive-control regression now passes: the configured
helper executes when explicitly enabled, and never during repaired root or
parent-commit scans (mock and canned live callbacks; zero provider calls).

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

The repair preserves read-only review and the future export-only act boundary.
`git_environment` strips inherited credentials/Git overrides, disables global
and system config and lazy fetching; `_git` pins an absolute executable and
disables fsmonitor, hooks, network protocols, replacement objects and recursive
submodules. Every diff path explicitly disables both helper types. Repository
local configuration is still read by Git; this is not a universal assurance
against malicious Git objects or vulnerabilities in Git itself. Output capture
still needs a resource bound in the later hardening phase.

The regression initially failed because Git required `/dev/null` in the
minimal worker. A character-device creation attempt was unusable in this WSL
environment; the final implementation bind-mounts just `/dev/null`, not `/dev`.
The positive control and Git reads then succeeded. No secret access, external
network access or controller-host exploit was performed.

## Why work initially stopped

Section 8 of the user-supplied Repo Steward directive requires stopping and
asking upon finding a route to a secret, network, or real-checkout modification:
“stop, document, do not quietly fix and move on.” A controller-side helper runs
with those capabilities. This is the required escalation, not a new approval
policy invented by the implementation agent.
