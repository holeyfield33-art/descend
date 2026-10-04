# Roadmap

## Current: Phase 2A launcher, real Nemotron with fake training

- Recovered the missing source/test/script tree from the supplied ZIP.
- Fake A/B worker runs through the Linux OS boundary and controller-owned JSON pipe.
- Frozen prediction, private hidden seed, filtered feedback and enforced budgets are tested.
- Registry, DSL, fake training, commitments and promotion run end to end.
- A controller-side Nano/Super inference loop adds provider usage accounting and durable $20 spend reservations.
- Paired evidence input matching, full runtime dependency lock, registry truncation anchors, and real local code/artifact hashes are implemented. See [Phase 2 status](PHASE2_STATUS.md); prior reports preserve their historical counts.

## Phase 2A: Nemotron viability with fake training

Execute four independent autonomous viability attempts from a clean commit. GO requires at least 3/4 protocol completions. Authenticated discovery confirmed `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`; inference and tool-call patterns are adapted from the pinned cookbook. Training/scoring remain fake in this gate.

Failed Nano and Super batches remain preserved. Live tool schemas now reflect remaining budgets and commitment order. `python -m scripts.audit_viability` verifies archived pilot evidence without provider calls. Current results and the experimental gate are recorded in [Phase 2 status](PHASE2_STATUS.md).

**Completed:** Super seeds 217–220 passed 4/4. Further viability calls are unnecessary for this gate. The next work is the real-training price/deployment gate; formal runs additionally require resolving the observed one-token provider-wrapper difference.

## Phase 2B: Real training and controller-owned evaluation

Choose a separate target only after training and deployment compatibility are confirmed. Adapt the official file-upload/job/checkpoint workflow, freeze actual artifact bytes, then validate deployment and controller-owned dev/hidden scoring. Do not infer current custom-model deployment support from the legacy notebook alone.

## Pilot and formal experiment

Run separate pilots, calibrate and freeze thresholds/budgets, then preregister 12 paired claim seeds. Retain failures under the preregistered policy.

## Later
- SM0 / SM1 / SM2 research tree (out of scope for this repo initially)
- No claim-bearing experiment, real target fine-tune or paid deployment has been run.
