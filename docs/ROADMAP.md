# Roadmap

## Current: Phase 1.6 partial, integrated CPU harness

- Recovered the missing source/test/script tree from the supplied ZIP.
- Fake A/B worker runs through the Linux OS boundary and controller-owned JSON pipe.
- Frozen prediction, private hidden seed, filtered feedback and enforced budgets are tested.
- Registry, DSL, fake training, commitments and promotion run end to end.
- Cookbook API research and offline request helpers are present; no cloud backend is enabled.
- Remaining foundations: actual A/B length matching, complete dependency lock, registry truncation anchor, and an independently reproduced published checkout. See [repair evidence](PROTOCOL_REPAIR_REPORT.md) and [release verification](RELEASE_VERIFICATION.md).

## Phase 2A: Nemotron viability with fake training

After the foundation gate, adapt the smallest official Nemotron inference/tool-calling example through the controller-side proxy. Verify autonomous operation and real provider token accounting before changing the training backend. Confirm the exact active agent model ID; the older Nano plan is not proof of current availability. See [API research](TOKEN_FACTORY_REFERENCE.md).

## Phase 2B: Real training and controller-owned evaluation

Choose a separate target only after training and deployment compatibility are confirmed. Adapt the official file-upload/job/checkpoint workflow, freeze actual artifact bytes, then validate deployment and controller-owned dev/hidden scoring. Do not infer current custom-model deployment support from the legacy notebook alone.

## Pilot and formal experiment

Run separate pilots, calibrate and freeze thresholds/budgets, then preregister 12 paired claim seeds. Retain failures under the preregistered policy.

## Later
- SM0 / SM1 / SM2 research tree (out of scope for this repo initially)
- No claim-bearing experiment, real inference call, real fine-tune or paid deployment has been run.
