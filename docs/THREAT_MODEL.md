# Threat Model (DM0) — Phase 1.6

## Repo Steward scope notice

The DM0 worker claims below do not cover Steward's controller-side Git reader.
The [helper-execution repair](STEWARD_BOUNDARY_REVIEW.md) disables Git textconv
and external diff helpers, with a Linux-isolated positive-control regression.
This does not cover arbitrary Git vulnerabilities. The user authorized repair
and continuation after the initial stop. Steward now has a restricted Linux
act worker with read-only source/runtime, namespace/UID isolation, resource
caps and a default-deny x86_64 syscall filter. It exports patches only.
See [scope and limits](STEWARD_ACT.md) and [automated attack coverage](STEWARD_ATTACK_MATRIX.md).
Independent review, arbitrary-repository support and kernel exploit assurance
remain unproven. The offline demo uses owned canned fixtures, not live proposals.

The approved 2026-10-06 live run rejected its first generated proposal for
invalid Python syntax before execution; no live patch was applied. This is one
observed refusal, not broad model/patch safety assurance. Every raw failure is
retained in the live report, with independent review still pending.

## Assets

- Hidden evaluation set and labels
- Promotion decision integrity
- Registry audit trail
- Candidate and prediction immutability after commit
- Controller configuration, secrets, and external API credentials

## Adversary

Arbitrary code produced by the agent, running with the permissions of the
Descend **agent isolation environment**.

## Assurance levels

### Level 1 — Protocol integrity (PASS for tested tool API)

The run-scoped pipe dispatcher enforces:

- no hidden data in agent manifests
- irreversible candidate/prediction commits
- no registry rewrite API
- budget enforcement
- one-shot hidden evaluation

### Level 2 — Execution isolation (PASS relative to integrated Linux tests)

The fake-agent launcher now invokes the namespace runner. A controller-owned dispatcher serves an explicit tool allowlist over inherited stdin/stdout pipes; no socket or controller filesystem is shared. Integrated hostile-worker tests exercise this same path. Unsupported hosts fail closed.

| Property | Mechanism (this environment) |
|----------|------------------------------|
| Network | `unshare --net` — empty network namespace; no egress |
| Filesystem | Mount namespace + **chroot** minimal root; only `/workspace` writable |
| PID | New PID namespace; host controller processes not visible |
| UID | Dropped to UID 65534 (nobody) when host is root |
| Secrets | Not present in agent environment; controller paths not mounted |
| Registry / committed artifacts | Live under controller root, outside agent chroot |
| TOCTOU | Freeze+rehash under controller ownership before hidden eval |

**Claim B wording (required):**

> Arbitrary code running with the permissions granted to the Descend agent
> isolation environment could not directly read or mutate controller-owned
> assets in the tested attacks.

This is **not** a claim of universal sandbox-escape resistance.

### Level 3 — Host/runtime security (out of scope for DM0)

Kernel exploits, compromised host root, malicious container runtime, and
side-channel attacks against the underlying OS are out of scope beyond normal
namespace/runtime assumptions.

## Residual risks

- Namespace isolation depends on a correct Linux kernel and `unshare` availability.
- Docker/OCI is preferred for portable judge demos; this host uses `unshare`+chroot when Docker is absent.
- A privileged process *outside* the agent namespace can still access controller data by design.
- Theoretical breakout via kernel bugs is not ruled out (Level 3).
- System runtime directories are read-only mounts. Controller assets must live outside them. `/workspace` and a size-limited `/tmp` are writable.
- Contamination feedback intentionally exposes only a pass/fail flag, as requested; it is not a zero-information response. Counts, similarity and hidden scores are excluded from tools and agent registry views.
- Run token accounting combines conservative serialized character/byte units with measured provider usage. Before each inference request, a token/cost reservation bounds the call. Controller-owned SQLite accounting caps all enabled inference calls at the authorized $20; uncertain outcomes retain their reservations. Real training/deployment remain disabled until their costs can also be bounded.
- See `PROTOCOL_REPAIR_REPORT.md` for remaining scientific and reproducibility gates; passing boundary tests does not establish measured model improvement.
- Token Factory inference runs controller-side. No provider SDK client, external tool or credential is exposed to the worker; proposals pass through the isolated JSON relay. The sibling cookbook is never mounted or imported. Current API/deployment limitations are documented in `TOKEN_FACTORY_REFERENCE.md` and `PHASE2_STATUS.md`.

## Acceptable outcomes

Failed adapters, rejected candidates, and null A-vs-B results are acceptable.
An experiment the agent can secretly manipulate is not.
