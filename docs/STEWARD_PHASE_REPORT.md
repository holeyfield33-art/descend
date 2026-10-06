# Repo Steward phase report

## WP4 automated boundary checks

Linux `/opt/steward-wp0-venv/bin/python -m pytest -q`: **197 passed, zero
skips**, 90.88 seconds. Windows `.venv\Scripts\python -m pytest -q -ra`:
**155 passed, 42 skipped** (first run 30.25 seconds). Recorded outputs are
`evidence/steward-wp4-linux.txt` and `evidence/steward-wp4-windows.txt`.
The 49 new attack cases include physical syscall/resource probes, six real Git
injection carriers with canned compliance, tamper rejection, 100 deterministic
JSON fuzz inputs and concurrent claims. See [coverage](STEWARD_ATTACK_MATRIX.md).

Git capture now bounds combined stdout/stderr to 2 MiB / 20 seconds and omits
stderr from errors. Finding parsing adds byte/depth/type limits. The worker
uses architecture-checked default-deny seccomp and IPC isolation. Pytest capture
is disabled so the 32 KiB controller output cap applies immediately. Trusted
verification requires the filter-installed flag and records bootstrap/filter
hashes. `doctor --require-act` passed its actual benign worker probe; output:
`evidence/steward-wp4-doctor.json`.

Initial localized failures: missing new capture-module copy in the isolated
Git fixture; socket creation denied before the network test's connection-only
assertion; doctor fixture mount root inaccessible to UID 65534. Repairs copied
the owned module, asserted denial across creation/connection, and set only the
owned probe root to 0755. Existing assertions were retained. The filter was
strengthened from a deny list to an explicit allowlist. A subsequent localized
suite passed 75 tests before the final reporter/doctor changes; the full suite
above validates those reporter changes, and the doctor probe was rerun after
its permissions correction.

`python -m scripts.check_steward_act_corpus --output controller_state/steward-act-corpus-v1-wp4`
rechecked all 24 known generator test/fix pairs: complete true, all
PATCH_VERIFIED, original snapshots unchanged, zero provider calls. New cards in
`evidence/steward-act-corpus-v1-wp4/` preserve kernel/filter identities separately
from historical WP3 cards. These are mock/oracle checks, not model quality.
Independent red-team review remains pending; [handoff](STEWARD_REDTEAM_HANDOFF.md).
Accounted spend remains $0.548195 across 118 historical calls; new real calls: 0.

## WP3 restricted act slice

Files: `act.py`, `act_worker.py`, `act_proxy.py`, offline act/corpus CLIs, two
test modules, doctor extension, scope/run documentation and provenance.
Controller decisions come from a trusted pytest reporter and hash checks.
All classification paths are exercised. The proxy's fake-client tests verify
zero caps, one-shot claims, no SDK retry and held ambiguous reservations.

Final full regression commands use the same interpreters/`-m pytest -q -ra` as
WP0: Linux **148 passed, zero skips**; Windows **119 passed, 29 skips**, all
reasons preserved in `evidence/steward-wp3-*-suite` equivalents
[`steward-wp3-linux.txt`](evidence/steward-wp3-linux.txt) and
[`steward-wp3-windows.txt`](evidence/steward-wp3-windows.txt).
Localized Linux act/proxy: 17 passed. A subsequent transport-options/doctor
check: 3 passed on Windows. Windows's four additional skips are act execution
requiring Linux namespaces; they are not passes.

Initial act tests: 4 failed / 9 passed because chroot reset cwd. After the
trusted bootstrap corrected cwd: 3 failed / 10 passed because short pytest
text omitted AssertionError's type. Replacing text inference with the trusted
exception/outcome hook resolved this. Existing tests were not weakened.

Command: `python -m scripts.check_steward_act_corpus --output controller_state/steward-act-corpus-v1` under Ubuntu.
Output: `{"complete": true, "cases": 24, "provider_calls": 0}`.
All 24 generator-known test/fix pairs classified PATCH_VERIFIED; original
snapshots were hash-checked unchanged. Cards/patches are in
[`evidence/steward-act-corpus-v1/`](evidence/steward-act-corpus-v1/).
These are **mock/oracle** proposals, not model generation success rates.

Scope deviation: initial act supports only `app.py::solve(values)` and simple
assertion tests in a restricted grammar. Unsupported real repositories refuse.
Scratch Git trees come from exact blobs without registering a Git worktree,
which avoids checkout helper execution and `.git` links to the real checkout.
Source is mounted read-only rather than writable; only a bounded tmpfs can be
written. Limits and concurrency caveats are in [STEWARD_ACT.md](STEWARD_ACT.md).
Kernel/runtime exploits remain outside measured assurance. WP4 attacks are next;
no final independent red-team grade is claimed. No additional real API calls.

## WP2 offline scoring and baseline results

Definitions: `STEWARD_METRICS.md`. Implementation: `scoring.py`, scoring CLI,
isolated baseline runner, `requirements-steward-eval-lock.txt`. Scorer tests:
3 passed, covering duplicates, invalid/wrong locations, clean/decoy alarms,
multiple findings, missing/error cases and Wilson values. A provider error
cannot earn recall from partial content. Full Windows regression: 131 collected,
106 passed, 25 skipped (same isolation/symlink reasons); the subsequent localized
provider-error check also passed. See `evidence/steward-wp2-windows.txt`.

Linux command:
`/opt/steward-wp0-venv/bin/python -m scripts.run_steward_baselines --output controller_state/steward-baselines-v1`.
Output: `{"cases": 44, "errors": 0, "provider_calls": 0}`. For each arm B0/B1:
`python -m scripts.score_steward_results --results controller_state/steward-baselines-v1/B1.json --output controller_state/steward-baselines-v1/B1-test --split test`
(substitute B0 for B1). Each yielded 32 cases, TP 0, FP 0, misses 16.
All raw outputs and hash identities are preserved under
`evidence/steward-baselines-v1/`; [EVALUATION.md](EVALUATION.md) lists all misses,
intervals and the intentionally weak baseline limitation. Adjudication sheets
and mappings are versioned exports; empty baseline sheets require no decisions.
Act verification and model metrics remain unmeasured. Additional spend: $0.

## WP1 frozen corpus and isolated label validation

Freeze commit `a810a3f` precedes all fixture execution. The 44 original seeded
cases comprise 24 bugs, 10 clean refactors, 4 hard negatives and 6 injection
decoys; split is 12 dev / 32 test. Test manifest SHA-256:
`e4893ad12a6d1e10863d43f5065ceaf9f0b88c2fbd565f9dd097d66d2db75043`.
Every snapshot, diff and bug reproducer is hash-pinned. Windows corpus rebuild,
hash/path rejection and execution-refusal tests: 3 passed.

Command from the workspace under Ubuntu root:
`/opt/steward-wp0-venv/bin/python -m scripts.check_steward_corpus --output controller_state/steward-corpus-validation.json`.
Output: `{"complete": true, "validated": 68, "expected_runs": 68, "provider_calls": 0}`.
Each of the 24 bug reproducers failed on reviewed code and passed on fixed code
(48 runs); all 20 clean/hard-negative/decoy snapshots passed their existing
smoke test. Execution occurred only inside the Linux namespace worker. Raw
per-case outputs, hashes, exit codes and runner identity are in
[`evidence/steward-corpus-v1-validation.json`](evidence/steward-corpus-v1-validation.json).

These are label checks, not model accuracy or patch-verification results.
The evaluator sees ground truth; future reviewer input must not. The frozen
review protocol is the unchanged existing reviewer source at `a810a3f`.
Repeated families across dev/test and weak existing tests limit conclusions.
No real-history cases or external evaluator data were added. No paid calls.

The manifest-freeze commit and subsequent validation commit are separate to
meet the requirement to commit the test split before its first run. Corpus
bytes remain unchanged; a Git attributes rule now prevents Windows CRLF
conversion of frozen diff files. No labels were edited after validation.

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
