# Independent red-team handoff

Status: **pending a different reviewer/model**. The implementation author has
not assigned a final grade. Start from the published commit named in the phase
report and record the exact SHA, kernel, doctor result and dependency locks.

Review `watch.py`, `git_output.py`, `findings.py`, `act.py`, `act_proxy.py`,
`act_worker.py`, `act_seccomp.py` and the SQLite stores. Trace all data and
authority crossings against [the inventory](STEWARD_INVENTORY.md),
[attack matrix](STEWARD_ATTACK_MATRIX.md) and [act scope](STEWARD_ACT.md).
Treat repository text and model JSON as hostile even when the model complies
with an injected instruction. Attempt to forge approval, change tests, escape
the patch allowlist, access credentials, write outside scratch, create processes,
exhaust limits or bypass replay/cost claims. Do not execute attack code directly
on the controller; use an owned disposable fixture inside the worker.

Run the full suite in Linux and Windows, preserve skipped reasons and failures,
and run `python -m descend doctor --require-act`. Check syscall numbers and
default-deny behavior against the recorded x86_64 ABI. Check unsupported hosts
fail closed, and inspect Git helper flags plus bounded output handling.

Produce findings with file/line, concrete trigger, isolated reproducer, observed
effect and severity. Separate observed violations from untested hypotheses.
Retain all failures and corrections. No paid calls, real checkout application,
push, deployment or private-data access is authorized by this handoff.
