# Repo Steward extraction plan

Plan only, 2026-10-05. No repository was created or extracted. The user will
provide the new repository. Preserve the [repair evidence](STEWARD_BOUNDARY_REVIEW.md)
and finish the package gates before representing an extraction as ready.

1. Copy an explicit allowlist from `descend/steward/` and its scripts/tests,
   including corpus/scoring, Git capture, act/proxy/worker/syscall filter and
   `scripts/demo_steward.py`. Preserve each source commit/hash.
   Retain parked fleet/context modules only if explicitly included in the new
   product; they must not become development priorities in this phase.
2. Extract the minimal controller environment parser, durable spend ledger,
   chat request helper, model IDs and price policy into owned local modules.
   Remove the incidental dependency on the broader DM0 inference module.
   Move the eventual audited worker and its boundary tests together.
3. Include the future corpus generator, versioned frozen manifests, scoring,
   mocked act tests, demo, public fixture licenses and static export builder
   only after their gates pass. Keep all failures and version identities.
4. Carry the MIT license, author attribution and source commit identities.
   Add per-file provenance for Descend reuse and any official cookbook
   adaptation; preserve applicable upstream attribution. Include the
   prior-work disclosure in the new README. Do not copy sibling checkouts.
5. Create a product-specific package manifest, Python version pin, dependency
   lock, LF attributes, ignore rules, CI and run manual. Verify Windows
   protocol tests and Linux isolated execution from a fresh public clone.
6. Publish only after reviewing an explicit file allowlist and secret/license
   scan. User supplies the remote; never infer it. Record source and destination
   SHAs and rerun the offline demo after extraction.

Stay in Descend: DM0 manifests, hidden evaluator, training adapters, experiment
registries, local-weight pilots and DM0-only scripts/tests/docs. Do not move
`.env`, private SQLite state, local reports, virtual environments, keys, caches,
held-out data, sibling references or unreviewed artifacts. Public pilot evidence
requires an explicit provenance/privacy review before any copy.

The standalone product must install and run without Descend or any codebook
checkout on the import path. Until extraction, keep this workspace intact.
