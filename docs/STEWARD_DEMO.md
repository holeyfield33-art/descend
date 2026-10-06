# One-command offline demo

From the repository root in provisioned Linux/WSL:

```bash
python -m scripts.demo_steward --output controller_state/my-new-demo
```

The output directory must be new. No `.env`, API key or network client is used.
The controller creates and commits its own disposable Git fixture. Canned
reviews demonstrate a clean warm-up, idle scan, new seeded bug, cited finding,
failing reproducer, passing unchanged reproducer plus existing test after a
minimal patch, and persistent restart deduplication. Target tests run only in
the restricted Linux worker. A second action claim is denied. The watched
fixture remains buggy and clean in Git: verification exports a patch; human
application requires a separate decision.

Outputs: `report.json`, local SQLite stores, `exports/` evidence card/patch and
`public/` static bundle. Publish only `public/`. The bundle contains escaped
HTML, owned fixture JSON, disclosed baseline tables, LICENSE and per-file
SHA-256 manifest. It has no script, action controls, external assets or private
SQLite data. Its build checks sensitive token patterns and a 500 KiB size cap;
this is a heuristic scan, not a guarantee about arbitrary sensitive content.

Native Windows execution refuses. On Windows open the committed
[`recorded static evidence`](evidence/steward-demo-public/index.html) for a
**recorded mock** view, or run the command under the provisioned WSL environment.
The measured [report](evidence/steward-demo-wp5.json) says PATCH_VERIFIED,
checkout unchanged, idle/restart calls zero and repeated action claim false.
This is a controller demo with a known finding/test/fix, not live model accuracy.
The demo is serial; do not run worker jobs concurrently under the shared UID.
