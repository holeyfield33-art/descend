# Repo Steward metrics v1 (predeclared)

Declared before model evaluation. Unit: a unique normalized citation
`(case, path, line, stripped evidence)`; repeated findings at that location/code
count once for TP/FP. Raw citation-valid rate retains every returned finding in
its denominator; malformed/missing citations are invalid. Model errors and
empty responses never drop a case and count as misses on bug cases.

- Citation-valid: evidence passes the existing added-line validator for this
  exact review diff. Report raw accepted / raw submitted findings.
- TP: unique citation-valid finding on a bug case, correct file, line in the
  generator's inclusive range expanded by two lines on each side.
- FP: every other unique citation-valid finding, including clean, decoy, hard
  negatives and wrong-location findings on a bug case.
- Recall: bug cases with at least one TP / all bug cases.
- Precision: TP / (TP + FP). Undefined denominators are null, never 100%.
- Clean false-alarm: clean cases (including hard negatives) with any FP / all
  clean cases. Decoy false-alarm is a separate proportion.
- Verification: reproduced TP findings / TP findings, and patch-verified TP
  findings / TP findings. Only controller act evidence may supply these fields;
  missing act evidence is explicitly unmeasured, not failed or passed.
- Latency, input/output tokens, conservative ledger cost and provider-reported
  usage: report per case and totals/median where available; missing stays null.

Report counts and Wilson 95% intervals (z=1.959963984540054) for proportions.
Small synthetic n and shared bug families limit generalization; these intervals
do not account for correlated cases. No p-values or significance claims.
Report all false-positive IDs and missed bug-case IDs, plus all provider errors.

B0 emits no findings. B1 runs only public existing tests and pinned ruff on
base and reviewed snapshots inside the worker; neither sees a fix or reproducer.
Only newly introduced failures/diagnostics with a source location on added
lines count. No source-attributed finding is invented from an unlocated test
failure. Record raw tool outputs even when no diagnostic can be attributed.

Blind adjudication presents only an opaque finding ID, explanation and snippet;
no model, arm, case label or ground-truth range. A separate private mapping
joins decisions later. Human decisions must be versioned and retained beside
automatic metrics. Until decisions exist, adjudicated metrics are unmeasured.
