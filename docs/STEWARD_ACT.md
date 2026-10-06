# Repo Steward act slice: supported scope and evidence

The controller accepts one bounded JSON proposal with `path`, `test_source`,
`replacement_source` and `expected_failure`. The current target is `app.py`
defining `solve(values)`, with simple assertion tests. Only a restricted Python
AST is supported; arbitrary repos, fixtures, imports, decorators, dynamic access,
conftest, sitecustomize and runner configuration refuse. This limited scope is
intentional and must be visible in the demo and submission.

The proposed test is hash-pinned before execution. The controller runs existing
tests first, then the new test on reviewed code, then exactly that original test
and existing tests on replacement code. A controller-owned pytest reporter
records exception classes and outcomes. Model claims about approval or tests
are ignored. Classification is `PATCH_VERIFIED`, `REPRODUCED`,
`NOT_REPRODUCED`, `PATCH_FAILED`, `TAMPERED` or `ERROR`.

## Worker limits

Linux namespaces/chroot, UID 65534, no capabilities/no-new-privileges, isolated
network/PIDs, read-only runtime and source. Only `/tmp` is writable: 8 MiB and
256 inodes. Limits: 15 seconds wall, 5 seconds CPU, 256 MiB address space,
one UID process (no forks/threads), 64 open files, 32 KiB captured output.
Source cap: 128 entries / 1 MiB; proposal 24 KiB, generated test 8 KiB,
replacement module 12 KiB. Source mounts are stricter than a writable worktree:
tests needing filesystem writes there are unsupported. Process quotas share
the nobody UID, so concurrent workers can refuse; run this slice serially.
Resource/privilege failures refuse; no Windows or unisolated fallback exists.

These mechanisms do not establish universal kernel/runtime escape resistance.
The system runtime mounts must contain no controller credentials or assets.
`/dev/null` alone is available from the host device tree. No controller object,
SDK, key or private state is exposed to the test process.

## Offline use

Provision the pinned runtime from `eval/README.md`. Inspect prerequisites with
`python -m descend doctor --require-act` on Ubuntu. It reports prerequisites,
not completion of red-team verification.

```text
python -m scripts.run_steward_act --case bug-off_by_one-1 --proposal controller_state/proposal.json --output controller_state/act-export
python -m scripts.check_steward_act_corpus --output controller_state/act-corpus-check
```

The first command takes an explicitly supplied **canned** proposal and one
mock finding. No model is called. The second uses generator-known tests/fixes
for all 24 bugs and is labeled **mock/oracle**. All 24 classified PATCH_VERIFIED
with original snapshots unchanged; this is controller plumbing evidence, not
generated-patch quality. Detailed outputs are recorded in the phase report.

For an owned Git fixture in the supported scope, `--repo`, `--sha`, `--finding`
and `--reviews-db` select an existing stored finding. The controller rechecks
the citation and reads exact committed blobs into an unregistered scratch tree.
It avoids checkout filters and any `.git` link to the watched checkout. No
branch, index or source file in that checkout is modified.

The separate action store atomically claims a finding before work. Default
per-commit cap is one; zero allows zero. Replays/crashes/errors are sealed, with
no automatic retries. Use a deliberately new state file only for a separate
labeled offline test run, never to bypass a live action limit.

The output is an evidence JSON card and, only for PATCH_VERIFIED, a `.patch`
export. There is no apply-to-checkout, push or PR command. Read the card's
limits, exact hashes and outputs before considering human application.

## Provider proxy

WP4 adds an architecture-checked, default-deny Linux x86_64 syscall filter loaded
after trusted pytest startup and before target collection. Unknown/x32 syscalls,
links, subprocess execution, process creation, network and namespace operations
are denied. Loading failures have no fallback. IPC is isolated too. Pytest
capture is disabled so the controller's 32 KiB output bound applies immediately.
Evidence records bootstrap/filter hashes, architecture and kernel. Run
`python -m descend doctor --require-act` to exercise the actual benign worker
probe, rather than relying only on executable availability.

`act_proxy.generate_proposal` adapts the existing official cookbook-derived
chat pattern into a one-call controller proxy. It requires an explicitly
supplied client, validates sensitive/bounded source and citation, claims the
action, reserves conservative spend, validates usage and proposal, and never
automatically retries. Tests inject fake clients and separate mock ledgers.
The CLI remains offline; live activation belongs to approved WP6 measurement.
