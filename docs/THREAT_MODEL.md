# Threat Model (DM0) — Phase 1.6

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
- Fake token accounting uses conservative serialized character/byte units. Real model integration must charge measured provider/tokenizer usage before it is enabled.
- See `PROTOCOL_REPAIR_REPORT.md` for remaining scientific and reproducibility gates; passing boundary tests does not establish measured model improvement.
- Token Factory request preparation is offline and controller-owned. No provider SDK client, external tool or credential is exposed to the worker; the sibling cookbook is never mounted or imported. Current API/deployment limitations are documented in `TOKEN_FACTORY_REFERENCE.md`.

## Acceptable outcomes

Failed adapters, rejected candidates, and null A-vs-B results are acceptable.
An experiment the agent can secretly manipulate is not.
