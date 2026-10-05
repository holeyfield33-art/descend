# Repo Steward phase report

## Authorized WP0 repair and baseline

**WP0 acceptance gate met:** repair commit `3af3ed9` was pushed, then freshly
cloned from `https://github.com/holeyfield33-art/descend.git` on both platforms.
Linux native checkout `/root/steward-wp0-fresh-3af3ed9`: 125 passed, zero skips.
Windows fresh checkout `controller_state/wp0-fresh-3af3ed9`: 100 passed,
25 skipped with the same reasons as baseline. Both used the installed locked
environments recorded by doctor; these were fresh source clones, not freshly
created second virtual environments. Both checkout statuses were clean.

Commands: `git clone https://github.com/holeyfield33-art/descend.git <destination>`,
then from the clone root `<locked-python> -m descend doctor` and
`<locked-python> -m pytest -q -ra`. Linux interpreter:
`/opt/steward-wp0-venv/bin/python`; Windows interpreter:
`C:\Users\SuperAdmin\.vscode\descend\.venv\Scripts\python.exe`.
Complete fresh-suite output is in `evidence/steward-wp0/fresh-*-suite.txt`.
The lock SHA-256 on both platforms is
`8d01bb9825baef3466071a82cbbe876d4754e728b5bc7b7ce2cbee2f41ee23ea`.

Provenance chain: initial inventory `1b7dad1`, authorized repair and baseline
`3af3ed9`, followed by this evidence-only closure. No evaluation result or act
capability is implied by WP0 completion.

The user authorized repair and continuation after checkpoint `1b7dad1`.
The initial stop recorded below is historical; no further continuation approval
is needed. New code: hardened Git invocations, offline `descend doctor`, platform
Python pins and LF source attributes. Worker compatibility: bind only `/dev/null`
so Git can run inside the jail. Existing tests were not removed or weakened.

| Command | Actual result |
|---|---|
| `.venv\Scripts\python -m descend doctor` | Protocol ready; no dependency mismatch; act readiness false |
| `.venv\Scripts\python -m pytest -q -ra` | 125 collected, 100 passed, 25 skipped, zero failures |
| `/opt/steward-wp0-venv/bin/python -m descend doctor` in Ubuntu | Protocol ready; namespace prerequisite available; act readiness false |
| `/opt/steward-wp0-venv/bin/python -m pytest -q -ra` in Ubuntu | 125 collected, 125 passed, zero skips/failures |

Full output and all 25 Windows skip reasons are preserved in
[`evidence/steward-wp0/`](evidence/steward-wp0/): unavailable Linux namespace
execution and one unavailable Windows symlink privilege. Windows skips are not
boundary passes. Doctor records interpreter invocation and binary separately,
absolute helper paths and the dependency lock hash. Linux uses 3.14.4; Windows
uses 3.14.6. Build-tool dependencies remain a reproducibility limitation.

The isolated helper positive control initially failed because the jail lacked
`/dev/null`. Creating a device node did not yield a usable device in this WSL
environment; the final single-device bind mount passed. The initial Linux full
run was 124 passed / 1 failed; final full run was 125 passed. No failures were
dropped from the report. Windows initially ran before doctor/probe additions:
99 passed / 24 skipped; final counts above supersede that intermediate result.

Ledger start/end: $0.548195, 118 calls, zero unresolved holds, no new calls.
Fresh public clone verification follows the repair commit before WP1 begins.
WP0 required a documentation stop checkpoint plus a repair commit, rather than
one commit, to preserve the mandated escalation and subsequent authorization.

## Initial checkpoint history

2026-10-05; WP0 checkpoint, not phase completion.
Source inspected: `b59a470231ec99d33ba297204dec9d4844c563ee`.

| Package | Actual status |
|---|---|
| WP0 | Static inventory and extraction plan drafted; blocked by controller-side Git helper execution path; new baseline/fresh-clone gate not run |
| WP1–WP5 | Not started; no corpus, scoring, act slice, attack matrix or complete offline demo delivered |
| WP6 | Not started; requires written cost approval after prerequisites |
| WP7 | Not started; current docs and operating reference updated without completion claims |

Documents added: inventory, extraction plan, boundary review, current run
manual, this report. No runtime code or tests changed. README and current
Steward-facing documentation point to the gate; historical experiment reports
retain their original evidence and counts.

## Environment evidence

Before the finding, the read-only prerequisite command
`wsl -d Ubuntu -u root -- bash -lc 'pwd; command -v python3; command -v unshare; command -v chroot; command -v git'`
returned exit 0 and:

```text
/mnt/c/Users/SuperAdmin/.vscode/descend
/usr/bin/python3
/usr/bin/unshare
/usr/bin/chroot
/usr/bin/git
```

`python3 --version` inside Ubuntu returned `Python 3.14.4`.
`unshare --mount --net --pid --fork true` returned exit 0. This is only a
namespace prerequisite probe, not an act worker test. The earlier WSL startup
timeout does not describe this session.

| Required check | This session |
|---|---|
| doctor | Not run: no such command in baseline |
| Windows protocol suite | Not run after stop condition; no current counts claimed |
| WSL full suite | Not run after stop condition; no current counts claimed |
| Fresh public clone suite | Not run; WP0 acceptance gate unmet |
| Corpus/reproducers/scoring/demo/export | Not implemented or run |
| Attack matrix / independent red-team | Pending; no final self-grade |

The previously reported 96 Windows passes / 24 Linux-only skips are historical,
not a substitute for a fresh baseline. No tests were newly skipped because no
test suite was invoked in this checkpoint.

## Spend and data handling

Start and end ledger read: cap $20; accounted upper bound $0.548195;
118 calls; zero unresolved holds; halted false at end. The end read used SQLite
read-only URI mode and aggregate queries, without loading credentials or
constructing a provider client. Additional paid calls: **0**; additional
accounted spend: **$0**. This is local accounting, not a provider receipt.

No fixture/model code was executed to exploit the finding. No sibling was
modified, no private evaluation data copied, and no extraction/deployment
performed. Secret scanning of the changed documentation is recorded with the
checkpoint commit validation; it must not be described as a universal absence
of secrets in every historical output. Command:
`.venv\Scripts\python controller_state/scan_steward_docs.py` returned exit 0:

```text
Document secret-pattern scan: 10 files; 0 matches.
Heuristic only; no credential values loaded or printed.
```

The local scanner checks private-key headers, common token prefixes and long
literal credential assignments in the ten changed Markdown files. Two earlier
stdin-based attempts failed with PowerShell encoding errors before scanning;
the saved UTF-8 script above completed. `git diff --no-ext-diff --no-textconv
--check` completed after removing a trailing blank line. These are documentation
checks, not product tests. This documentation checkpoint is the sole WP0 commit
in this session; it is deliberately incomplete and identified by commit subject
`docs(steward): record WP0 boundary gate and operating reference`.

## Required decision

See [the proposed repair](STEWARD_BOUNDARY_REVIEW.md). The directive requires
asking before proceeding after this discovery. Resume WP0 only after the
human authorizes addressing it. All later work and the complete engineering
manual remain pending. There are no new evaluation numbers, false-positive
rates, or verification-rate claims to report.
