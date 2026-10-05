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
