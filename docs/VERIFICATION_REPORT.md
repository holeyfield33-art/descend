# Descend repository verification and recovery

Audit date: October 3, 2026 (America/Los_Angeles).

This is the historical recovery audit. Subsequent fixes and current test results are recorded in `PROTOCOL_REPAIR_REPORT.md`; the blockers below describe the state at the time of this audit.

The user's request was to verify the existing clone against the supplied ZIP and recover missing files. The handoff was treated as supporting project context and reported claims, not as independently verified evidence or permission to start cloud integration.

## Initial public state

- Origin: https://github.com/holeyfield33-art/descend.git
- Branch: `main`.
- Workspace HEAD and live `git ls-remote origin refs/heads/main`: `29c22fceb320c0b260a85ed60d5dfffcc48e7457`.
- Initial `git status --short`: empty (clean).
- Tracked file count: 30. Generated environments and Git internals are excluded from source counts.
- No repository `AGENTS.md` was found.
- `import descend`: PASS. Controller, sandbox, registry, DSL, manifest and evaluation imports: FAIL with missing-module errors.
- Initial `python -m pytest -vv`: 0 collected, no tests ran, exit 5, 0.05 seconds. This was the installed host pytest before recovery; no clean-environment initial test success is claimed.
- A fresh Windows virtual environment installed `.[dev]` successfully. Installation alone did not establish package completeness.

The public README's A/B/C PASS claims and historical 27/45-test reports were not reproducible from that public tree.

## Recovery

Source: `C:\Users\SuperAdmin\Downloads\descend.zip`.

ZIP SHA-256: `80be70a324775f3de062867890efc25830e982b8d82af8aabb3dcaca846b3f86`.

The ZIP's main ref contains `9fec2cb580cd60652728f3efec75e216cbc6f771`; it also contains the earlier reported local commit objects. Its Git metadata was inspected as data and was not installed into the workspace.

Recovered 49 missing files: 27 package implementation files, 14 test files, three scripts and five documentation files. `RECOVERED_FILES.txt` lists every recovered path. The source tree now has 82 files including the added script package init, this report and its inventory (excluding generated artifacts).

No ZIP `.git`, `.venv`, bytecode, controller state, credentials, or generated run artifacts were imported. Existing files were compared after normalizing line endings. Three substantive differences were comments/docstring text and were retained from the clone; the sandbox exports and generated-state ignore rules were recovered. The corrupted control character in the ZIP's top-level package docstring was not imported.

Additional small repairs:

- Non-POSIX isolation availability reports unsupported operation instead of calling absent `os.getuid`/`os.geteuid` functions.
- Package discovery includes `scripts`, and `scripts/__init__.py` was added so the advertised installed CLI has its implementation packaged.
- README and threat-model status now distinguish standalone runner tests from integrated security guarantees.

At this initial audit, recovery changes were local and uncommitted; nothing had been pushed and a fresh public clone still lacked the recovered files. Current publication and clean-checkout evidence are recorded in `RELEASE_VERIFICATION.md`.

## Reproduced results

| Check | Result | Evidence / limit |
|---|---|---|
| Fresh editable install | PASS | Windows Python 3.14.6; Linux/WSL Python 3.14.4 |
| Distribution wheel | PASS | Standard isolated wheel build succeeds; all four scripts package files included |
| Seven requested imports | PASS after recovery | All explicitly imported in Windows venv |
| Windows pytest | PASS for executed tests | 55 collected; 45 passed, 10 skipped; 3.73s; no failures/errors |
| Linux pytest as root in WSL Ubuntu | PASS | 55 collected; 55 passed; no skips/errors/failures; 4.59s |
| Fake A, seed 42 | PASS | Completed, PROMOTE, synthetic delta 0.423588427289759 |
| Fake B, seed 42 | PASS | Completed, PROMOTE, same synthetic delta |
| Installed CLI / scripted C, seed 42 | PASS | Completed, PROMOTE, synthetic delta 0.5153468429728754 |
| Registry verification for A/B/C | PASS | Each chain valid with 11 expected events |
| Frozen-file tamper checks | PASS for tested attacks | Candidate, prediction and candidate adapter-hash mutations detected |
| Standalone direct egress | PASS for tested probes | TCP 1.1.1.1:443 and example.com DNS blocked in new net namespace |
| Standalone controller-file access | PASS for tested paths | Standard controller paths absent; backing files remain on host |
| Standalone secret scrub | PASS for tested probes | Planted environment keys absent |
| Standalone PID/UID isolation | PASS for tested probes | UID 65534 and new PID namespace |
| Integrated controller access / egress | NOT YET PROVEN | FakeAgent gets the Controller object in-process; no secured tool transport |

Fake scores are deterministic hash-derived plumbing fixtures, not measured model improvements. These runs do not constitute DM0 research results. Docker CLI exists, but its daemon was unavailable; no Docker execution is claimed. Linux environment creation used a fresh venv with pip bootstrap because Ubuntu lacked ensurepip.

## Reconciliation with completion reports

| Item claimed | Public tree before recovery | Recovered / checked | Status and limits |
|---|---|---|---|
| Controller and budgets | Package init only | Present; flow/counter tests pass | Broader enforcement incomplete |
| Registry, events, hashchain | Partial | Present; tests and trial chains pass | Empty/truncated chain accepted without expected-length anchor |
| DSL primitives/generator/splits/grader | Init only | Present; deterministic tests pass | Hidden split shares disclosed seed |
| Manifest schema/build/neutral | Init only | Present; imports work | B matches dummy A rather than actual A |
| Candidate identity/validation | Init only | Present; tests pass | Base/evaluator/controller/promotion hashes are stub constants |
| Evaluation/contamination/statistics | Evaluator and init | Present | Contamination feedback leaks hidden-derived signals |
| Fake agent/backend and Arm C | Missing implementations | A/B/C flows pass | Trusted in-process plumbing, no real training |
| Candidate/prediction commitments | Missing controller | Tested basic commits | Prediction remains mutable in decision path |
| One-shot hidden evaluation | Missing controller | Duplicate evaluation test passes | Optimization methods not closed after commit/reveal |
| TOCTOU | Missing controller | Three recovered tests pass | Actual adapter/dataset bytes not frozen; prediction decision uses memory |
| isolation.py / secret scrub / path jail | Missing | Present; soft isolation tests pass | Soft subprocess runner remains exported |
| Dockerfile.agent | Present | Retained | Docker runtime not wired into harness |
| unshare/chroot/network/PID isolation | Missing runner | Runner plus 10 tests recovered; Linux tests pass | Standalone only; incomplete attack matrix |
| Adversarial tests / scripts | Empty test init; no scripts | 14 test files and three scripts recovered | Full restored suite has 55 tests |
| Threat model / spec delta / provenance | Threat model only | Missing docs restored; status corrected | Original PASS language exceeded evidence |
| Clean-clone instructions / dependency lock | Present | Editable installs work | Lock is not complete: jsonschema uses a range, transitives unpinned |

## Confirmed blockers beyond passing tests

1. No integrated hard boundary. `FakeAgent.run` receives the controller itself. `run_agent_script` uses ordinary same-user subprocess execution; `run_in_hard_isolation` is only called by standalone tests. A narrow isolated-agent tool loop does not exist yet.
2. Hidden-derived optimization feedback: `create_dataset` returns contamination flags, overlap counts and similarity computed against hidden examples, and logs them to an unfiltered registry view.
3. Post-commit prediction mutation: after running a fake candidate and hidden evaluation, setting the retained prediction's `predicted_target_delta` to 999 makes `decide` report 999.0. Frozen prediction integrity does not govern the decision input.
4. Action cap bypass: `BudgetState(actions_max=0).record_training()` succeeds and increments actions to 1. Wall-clock, token and generation bounds are not comprehensively enforced; promotion passes `budgets_respected=True` unconditionally.
5. Seed exposure: the same seed builds DSL and hidden splits; the fake agent is given that seed. Hidden sets can be reconstructed from public generator code.
6. Unfiltered registry view includes the `hidden_eval` payload after reveal. The controller does not expose a properly scoped read-registry method, despite the tool module's claim.
7. Treatment mismatch: default A evidence is 442 JSON characters; B neutral content is 324 characters. Both arms share operational content, but the intended length matching is not established.
8. Identity binds placeholder code hashes and an empty controller transcript; no actual training artifact bytes are available in this fake phase. Do not carry these stubs into claim-bearing experiments.
9. The recovered hard tests do not actively attempt every required guessed-path, symlink, hardlink, registry-write, host-gateway or metadata attack. The mock proxy test calls a local echo function outside isolation; it does not verify an agent-to-controller transport.
10. Runner hardening remains: host system directories are bind-mounted, memory_mb is unused, ancestor/workspace permissions are broadly relaxed, shell paths are substituted without safe quoting, and availability checks presence rather than actual privileges. These need targeted review before integration.

Claim A: **FAIL** against the intended protocol guarantees (mutable decision input and hidden-feedback exposure). Some narrower API tests pass.

Claim B: **NOT YET PROVEN** for the integrated harness; standalone Linux probes pass.

Claim C: **NOT YET PROVEN** for the integrated harness; standalone Linux probes pass.

Phase classification: **PHASE 1.6 PARTIAL** for the recovered local tree. The original public tree was **PHASE 1 INCOMPLETE**. Earlier protocol defects remain even though a standalone Level 2 runner now executes successfully.

Phase 2A is blocked. Finish protocol enforcement and the integrated isolated tool loop, expand adversarial coverage, then commit/publish the recovered tree and verify another clean checkout. No Nemotron, Nebius, GPU, paid-cloud or claim-bearing experiment was started.
