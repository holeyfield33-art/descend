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

### Level 1 — Protocol integrity (PASS)

The controller API exposes no forbidden state changes:

- no hidden data in agent manifests
- irreversible candidate/prediction commits
- no registry rewrite API
- budget enforcement
- one-shot hidden evaluation

### Level 2 — Execution isolation (PASS relative to tested threat model)

Agent code runs under OS-enforced isolation:

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

## Acceptable outcomes

Failed adapters, rejected candidates, and null A-vs-B results are acceptable.
An experiment the agent can secretly manipulate is not.
