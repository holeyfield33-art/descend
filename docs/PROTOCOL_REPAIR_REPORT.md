# Protocol and integrated-boundary repairs

This report supersedes the five priority blockers in the historical `VERIFICATION_REPORT.md`. It records the repair verification milestone; current publication and clean-checkout evidence are in `RELEASE_VERIFICATION.md`. No cloud work or research experiment was run.

## Implemented

1. **Real worker boundary.** `FakeAgent` is now a trusted host launcher. Its compatibility signature still accepts the controller on the host; the executable worker receives only serialized operational content and JSON pipes. Worker code runs in new mount, PID and network namespaces, chrooted as UID 65534. No controller object, private seed, controller mount or listening tool socket crosses the boundary. The controller serves an explicit run-scoped allowlist: dataset generation, fake training, capped dev feedback, commitments and a filtered registry view. Hidden evaluation, promotion and other runs cannot be requested. Unsupported hosts fail closed with no ordinary-subprocess fallback.
2. **Frozen prediction controls the decision.** Inputs are copied at commitment, stored in controller-owned storage and hashed. `decide` rechecks artifacts and loads its prediction from that frozen file. Mutating the original input or in-memory prediction cannot alter the decision. File tampering after reveal is rejected. Predictions require finite numeric values, valid intervals and the exact permitted fields.
3. **Contamination feedback is a bare flag.** Dataset responses and dataset registry entries include only `contamination: {passed: true|false}`. Overlap counts, similarity and match details stay out of those surfaces. Agent registry views use an explicit event/field allowlist and exclude hidden evaluation, decisions and backing-chain hashes. Agent registry access closes after reveal. This implements the requested flag policy; a flag still conveys some information and should not be described as zero leakage.
4. **Private evaluation seed.** The controller creates an independent 128-bit random hidden seed. Paired runs within the same controller share it; different experiment seeds receive separate values. Hidden strings cannot be regenerated from the disclosed DSL/run seed. Private replay metadata is stored only under the controller's hidden directory. A trusted caller can supply a frozen hidden seed for reproducible reruns; that option is absent from the tool transport.
5. **Budgets hold.** Training and dev calls check the action cap before advancing their counters. Commitments and rejected requests also consume actions. Cumulative generation limits are run-owned and survive restarting a tool session. Training volume includes epochs. Token-volume and monotonic wall-clock checks halt over-budget workers, and promotion evaluates the real budget state. Optimization tools close at candidate commitment; only the separate prediction commitment remains available. A second decision is rejected.

Additional runner hardening: fixed minimal PATH, bounded 64 KiB request lines, bounded message queue, sanitized tool errors, wall-clock deadline, process-group cleanup, kill-child behavior, address-space limit, safe shell path quoting, no-new-privileges and an empty capability bounding set. Controller/workspace trees must be disjoint; controller assets cannot live in system runtime mounts. Existing workspace symlinks and hardlinks are rejected. Ancestor permissions are no longer relaxed.

## Verification

| Environment | Result |
|---|---|
| Linux / Ubuntu WSL, trusted root launcher | 76 collected, 76 passed |
| Native Windows | 76 collected, 53 passed, 23 skipped |
| Integrated fake A/B trials, seed 42 | Completed; controller performed one hidden evaluation; both registry chains valid |
| Whitespace check | `git diff --check` passed |

The new tests reproduce mutable-prediction attacks, post-reveal frozen-file mutation, private seed separation and paired equality, filtered contamination/registry feedback, zero action caps, training/dev caps, token/time bounds, cumulative generation, denied tools, malformed/oversized transport and fail-closed runtime behavior.

An integrated hostile worker attempted absolute/traversal paths, `/proc/1/root`, symlinks, hardlinks, controller/registry writes and deletion, secret environment inspection, public TCP, localhost, host-gateway and metadata addresses, and DNS. Those attempts failed in the tested environment. The same worker successfully requested approved dataset generation over the controller pipe. A zero-action-cap worker halted without creating a dataset or candidate.

Claim A: **PASS for tested run-scoped tool API**.

Claim B: **PASS relative to the integrated Linux threat model and tested attacks**.

Claim C: **PASS relative to the integrated Linux threat model and tested TCP/DNS attacks**.

Windows skips these Linux worker tests rather than simulating security. Linux without the required namespace/chroot privileges also fails closed. Docker is not the active runtime. Legacy `run_agent_script` remains a soft test helper and is not exposed through the worker transport.

## Remaining gates

Phase 2A remains gated on the outstanding prerequisites. Publication and clean-checkout status are recorded separately in `RELEASE_VERIFICATION.md`. The audit's A/B length mismatch, incomplete dependency lock and registry truncation anchor are still outstanding. Fake base/code hashes, synthetic evaluator/backend and provisional token accounting remain explicit stubs. No real adapter bytes are frozen in this fake-training phase. Official Token Factory examples have been inspected and adapted into offline controller request helpers; no live client is wired into the agent transport. See `TOKEN_FACTORY_REFERENCE.md`.

Fake token accounting charges conservative serialized character/byte volume and generated ASCII training length multiplied by epochs. It is bounded but does not measure real model tokens; a provider/tokenizer must supply measured usage before real model integration. The sandbox uses read-only host runtime directories and per-process memory limits, not a minimal OCI image or aggregate cgroup resource limits. Host/root compromise and kernel exploits remain outside DM0's scope.

The historical recovery audit describes the earlier broken state; it should not be read as the current result. Passing these tests establishes tested harness behavior, not model-improvement evidence or readiness to spend cloud credits.
