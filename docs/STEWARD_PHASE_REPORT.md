# Repo Steward phase report

## Specialization-framework review and gap plan — 2026-10-06

Reviewed Descend at `c1e6d0fa6e810aa45cc0daaa855826746baeab18` against the clean
local RSEF checkout and matching remote HEAD
`b810d8b397d2858a2693a8232599a5982dd25a19`. The
[gap register](STEWARD_GAP_PLAN.md) records 13 reference-framework findings and
32 known product/evaluation/submission gaps, with evidence, priorities and
completion criteria. Main reuse candidates are bounded source-bound packs,
dependency context and provenance; the RSEF verification gate and simulation
scores must not supply Steward execution or quality evidence.

This was a static source/artifact review, not independent security clearance.
No reference checkout edits, paid calls, training or new evaluation occurred.
Official submission requirements and deadline were checked against the linked
rules. Existing live records and sealed corpus/run claims remain unchanged.

## WP6 live completion and documentation — 2026-10-06

Final public-clone validation at `5bc1652`: Linux **205 passed, zero skips**,
55.51 seconds; Windows **161 passed, 44 explicit skips**, 42.36 seconds.
Both used the same locked environments and `-m pytest -q -ra`; doctor passed
the actual Linux worker. Full outputs are `evidence/steward-live-fresh-*`.
No provider calls were made by these tests or report regeneration.

The cross-host export check exposed root LICENSE line-ending differences and
one UTF-8 em dash decoded using Windows's implicit code page. Root LICENSE is
now pinned LF; exporter JSON reads explicitly use UTF-8. A stronger Unicode/HTML
test passes with 3 exporter tests on each platform. Final regenerated data,
HTML, LICENSE and manifest are **byte-identical across Windows and Linux**;
the bundle is **63,525 bytes**. Raw API records and measured scores were not
changed. The historical mock bundle retains its original recorded byte hashes.
The first cross-host comparison failed; its cause and repair are recorded here,
with passing hashes in `evidence/steward-live-cross-platform-bundle.json`.
The original larger bundle size below is the pre-portability-fix checkpoint.

Final audit: 244 public files, zero sensitive-pattern matches; every raw-record
and bundle hash valid, copied license matches, end ledger still $0.613690 across
223 calls with no unresolved holds. The scan is heuristic, not invoice or
universal secret-exclusion proof. No extra live attempt followed the act halt.

The user explicitly approved the cost plan. Controller-only approval text named
frozen v4 SHA `f3e07c9831152bf60ecf8a4638a6f41bec02decbc85680fce5bec95fa07e47ce`
and the $8 additional cap. Command under Ubuntu, from the Descend root:
`/opt/steward-wp0-venv/bin/python -m scripts.run_steward_live --plan eval/steward-live-plan-v4.json --approval controller_state/live-approval.txt --output controller_state/steward-live-20261006`.
The plan hash check and actual worker probe passed before key/client use.

Result: **105 provider calls** — all 64 primary reviews, all 40 repeats, one act
proposal. SDK transport errors: zero. Super had seven primary response-schema
errors; six were pseudo timeout/error text in model content, not observed SDK
timeouts. Raw responses and provider usage/IDs are retained without retries.
The invalid act source contained literal backslash-n sequences and failed Python
syntax validation before any live generated code ran. The run halted acts;
seven other candidates are NOT_RUN. No live patch was verified, exported or applied.
The global spend ledger is not financially halted; the corpus/run claims remain
sealed. No prompt/schema repair, result deletion or frozen-test rerun occurred.

Automatic primary scores: both recall 15/16; Super precision 16/17, clean alarms
0/11 with seven schema failures; Nano precision 15/29, clean alarms 11/11.
Both repeat subsets were stable on 9/10 cases by accepted-citation/parse-status
signature. One proposal was attempted, zero verified; the denominator is one,
not all eight candidates. These are weak location metrics on correlated seeded
functions, not human-adjudicated general accuracy. Full Wilson tables and every
FP/miss/error: [STEWARD_LIVE_RESULTS.md](STEWARD_LIVE_RESULTS.md).

Ledger start/end: $0.548195 / **$0.613690**, 118 / **223 calls**,
zero unresolved holds at end, $20 cumulative cap, halted false, no billing
receipt. Additional accounted upper bound **$0.065495**; observed usage
32,322 prompt + 11,641 completion tokens. The approved $6.40 stop threshold
was not reached; validation failure ended acts instead.

Public evidence retains 223 original JSON files plus derived repeat metrics,
with per-file SHA-256 manifest, under `evidence/steward-live-20261006/`.
SQLite, environment and approval files are excluded. All raw JSON passed the
sensitive-content heuristic. The live static bundle is 63,551 bytes, has no
script/action controls, copies LICENSE and includes a hash manifest. It is
separate from the recorded mock demo; no deployment occurred.

The new offline export command validates owned case identities and sensitive
patterns before writing output; hostile HTML is escaped. Export tests: **3 passed**
on Windows, including secret-like output and unowned-identity rejection.
Command: `python -m scripts.export_steward_evaluation --source docs/evidence/steward-live-20261006 --output controller_state/new-live-export`.
User-facing docs were reconciled; historical reports/counts remain labeled.
Independent red-team review, blind human adjudication, human deployment/video
and destination-repository extraction remain pending. No sibling was modified.

## WP6 preparation — offline only

Final published-code gate at **`46428f9ce74d3d69b35ce43e82ad1cfe9f82ccde`**:
fresh public Linux clone `/root/steward-wp6-fresh-46428f9` **202 passed, zero
skips**, 88.80 seconds; fresh public Windows clone
`controller_state/wp6-fresh-46428f9` **158 passed, 44 explicit skips**, 61.76
seconds. Commands: the installed locked interpreter with `-m pytest -q -ra`.
Both Git statuses were clean. Final plan `--check` passed on both platforms;
Linux `doctor --require-act` passed. Public bundle hash verification passed
after the Windows clone. Complete suite/skip output and doctor/plan manifests:
`evidence/steward-wp6-fresh-*`. Environments were reused, not newly created.

Intermediate workspace suite: Linux 201 passed / zero skips in 303.22 seconds
(before the final approval-mismatch test was added); Windows 157 passed /
44 skips in 61.16 seconds. The shared-drive Linux suite experienced a long
filesystem wait; the native Linux clone was faster. An owned-process stop probe
matched no running test by its exact log descriptor; the original suite completed.
The final fresh-clone run above includes the approval and corpus-replay checks.

Start/end shared ledger read in SQLite read-only mode: cap $20, accounted upper
bound $0.548195, 118 calls, zero unresolved holds, halted false, no provider
receipt. **Additional real calls 0; additional spend $0.** Fake clients use
separate temporary ledgers. No sibling mutation, private-data import, deployment,
extraction, real-checkout application or unauthorized communication occurred.
Next live gate is written approval of the frozen quantified plan, not permission
to continue ordinary offline work.

Final public-artifact scan covered **82 files**, with zero private-key/common
long-token-prefix matches. Bundle file hashes and copied LICENSE matched.
No credential values were loaded for this scan; it remains heuristic.

Published WP5 `3262367` fresh public clones passed: Linux **198 passed, zero
skips** (57.71 seconds), Windows **155 passed, 43 skipped** (46.68 seconds).
The native Linux clone ran doctor and the offline demo successfully. These
checks reused the installed locked environments rather than new virtualenvs.
Outputs are `evidence/steward-wp5-fresh-*.txt` and the doctor JSON.

The paid workload is prepared but has made **zero live calls**. The reviewer
now accepts an explicit priced model and bounds its serialized request to
20 KiB; prompt text is unchanged. The act verifier records explicit mock/live
proposal origin. The runner records raw requests/responses, retains errors,
separates primary/variance scores, runs acts after all reviews, limits additional
reservations and seals the plan/corpus against replay. Provider credentials and
client construction follow the exact approval/hash/doctor/ledger gates.
SQLite spend/review/act contexts now explicitly close connections after their
transactions; the long fake workload exposed retained descriptors from Python's
transaction-only connection context. Existing atomic-claim semantics remain.

Offline contract checks: Windows 20 passed / 5 Linux skips; Linux 20 passed.
The full fake workload exercised 104 review requests across both models; a
separate Linux fake-provider proposal went through the real filtered worker and
verified its patch after all reviews. None of these are paid model results.
Final config is `eval/steward-live-plan-v4.json`; v1–v3 are retained preparation
snapshots, never executed live. Current plan SHA-256:
`f3e07c9831152bf60ecf8a4638a6f41bec02decbc85680fce5bec95fa07e47ce`.
Hash check returned provider_calls 0. Proposed maximum 112 calls, conservative
reservation bound $5.357024, requested new cap $8, stop threshold $6.40,
remaining cumulative ceiling after maximum reservations $14.094781.
Written approval is still required. Independent red-team review, measured model
evaluation, hosted deployment and new-repository extraction remain pending.

## WP5 offline demo and static export

`python -m scripts.demo_steward --output controller_state/steward-demo-wp5`
under the provisioned Ubuntu controller returned complete true: one new bug
finding, PATCH_VERIFIED, watched source unchanged, zero idle/restart mock calls,
duplicate action denied and zero provider calls/cost. Two canned reviews cover
the clean warm-up and seeded bug. Report and static bundle:
`evidence/steward-demo-wp5.json`, `evidence/steward-demo-public/`.
No provider quality is measured. The HTML is escaped, static and has no action
controls or external resources. The LICENSE matches the repository; every
bundle hash verified. A public-file scan covered 64 files with zero private-key
or long common token-prefix matches; this is heuristic and no credential
values were loaded. The demo integration test exercises the actual Linux worker:
1 passed in 4.32 seconds, repeated after adding exported baseline intervals
(1 passed in 4.67 seconds). Native Windows localized checks: doctor 1 passed,
demo 1 explicit Linux-only skip. An intervening WSL startup attempt failed with
`Wsl/Service/CreateInstance/CreateVm/0x800705b4`; no distributions were running.
`wsl --shutdown` and a fresh invocation recovered it. The final public scan
covered 66 files with zero matches; current bundle hashes/license verified.

Local Git incident after WP4 commit: `refs/heads/main` contained 41 NUL bytes.
Its reflog and readable commit object independently identified
`c720592faa915515d06d5f81bc01887b66ea5c6d`. The damaged bytes were saved in ignored
controller state and that exact reference restored with an atomic write/fsync.
No reset, history rewrite or worktree replacement occurred. Cause is unknown;
do not infer a worker escape from an unexplained host metadata incident.
WP4 code/evidence commit: `c720592`; prior WP3 commit: `3caa90f`.

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
