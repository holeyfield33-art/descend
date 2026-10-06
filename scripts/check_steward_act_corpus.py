"""Mock/oracle act proposals across frozen bug cases; no model performance claim."""
import argparse
import json
from pathlib import Path

from descend.steward.act import verify_proposal
from descend.steward.corpus import canonical, verify_manifest
from descend.steward.findings import added_lines


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("eval/v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest = verify_manifest(args.corpus)
    rows = []
    for case in manifest["cases"]:
        if case["label"] != "bug":
            continue
        directory = args.corpus / "cases" / case["id"]
        diff = (directory / "review.diff").read_text(encoding="utf-8")
        (path, line), evidence = next(iter(added_lines(diff).items()))
        finding = dict(path=path, line=line, evidence=evidence, severity="low", reason="MOCK/oracle seeded finding", verification="Controller test")
        expected = {"empty_check": "IndexError", "exception": "IndexError", "encoding": "UnicodeDecodeError"}.get(case["category"], "AssertionError")
        raw = json.dumps(dict(path="app.py", test_source=(directory / "test_reproducer.py").read_text(encoding="utf-8"),
                              replacement_source=(directory / "fix/app.py").read_text(encoding="utf-8"), expected_failure=expected))
        result = verify_proposal(directory / "review", finding, raw, args.output / case["id"], review_diff=diff,
                                 identity={"seeded_case": case["id"], "corpus_version": manifest["version"],
                                           "test_manifest_sha256": (args.corpus / "test-manifest.sha256").read_text().strip()})
        rows.append({"case": case["id"], "classification": result["classification"], "source_root_unchanged": result["source_root_unchanged"]})
    complete = len(rows) == 24 and all(r["classification"] == "PATCH_VERIFIED" and r["source_root_unchanged"] for r in rows)
    report = {"kind": "mock/oracle", "complete": complete, "cases": rows, "provider_calls": 0,
              "limitation": "Known generator tests and fixes; no model-generated proposals or review accuracy measured"}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_bytes(canonical(report))
    print(json.dumps({"complete": complete, "cases": len(rows), "provider_calls": 0}))
    raise SystemExit(0 if complete else 1)


if __name__ == "__main__":
    main()
