# Repo Steward seeded corpus

Version 1 is an owned MIT-licensed synthetic corpus, generated with seed
20261005. It contains 24 bug cases in 12 categories, 10 clean refactors,
4 hard negatives and 6 separately labeled injection decoys. Dev has 12 cases;
the frozen test split has 32. It includes no third-party code or evaluator data.

Generate into a new empty directory with:

```text
python -m scripts.build_steward_corpus --output controller_state/corpus-rebuild
```

The generator does not execute source. Each case has base/review/fix snapshots,
a review diff, a fix diff and SHA-256 hashes. Bug cases have an independent
pytest reproducer and generator-defined location. The test manifest must be
committed before validation or model evaluation. Labels and fixes are evaluator
data, never review prompt inputs. Model prompts freeze before the first test
review; no prompt iteration has occurred on this split.

These are tiny easy cases with repeated families across splits. The public
existing tests deliberately only check the API exists. This is a measurement
of a narrow seeded task, not general repository review accuracy. Ground-truth
location matching alone is weak. No real-history performance claim is possible.
Reproducers require isolated Linux validation before WP1 is complete.

Frozen source commit: `a810a3f`; test manifest SHA-256:
`e4893ad12a6d1e10863d43f5065ceaf9f0b88c2fbd565f9dd097d66d2db75043`.
`review-protocol-v1.json` records the existing reviewer source/parameters.
Corpus v1 bytes are exempt from Git line-ending conversion so hashes survive
Windows and Linux checkouts. A changed corpus requires a new version.

The current label checker uses a trusted pytest 9.1.1 runtime at
`/usr/local/lib/steward-test-runtime/bin/python` within the read-only `/usr`
mount. Provision only dependencies there, never keys or controller state:

```bash
python3 -m venv /usr/local/lib/steward-test-runtime
/usr/local/lib/steward-test-runtime/bin/python -m pip install pytest==9.1.1
python -m scripts.check_steward_corpus --output controller_state/corpus-validation.json
```

The checker refuses Windows and unavailable Linux isolation. This checks owned
fixtures; it is not the future hostile-model-code executor or its resource-limit
assurance. Controller environment and provider clients are absent from the worker.
