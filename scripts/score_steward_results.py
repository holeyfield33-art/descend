"""Score exported results; never call a model or execute a fixture."""
import argparse
import json
from pathlib import Path

from descend.steward.corpus import canonical, verify_manifest
from descend.steward.scoring import blind_sheet, score_results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("eval/v1"))
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--split", choices=["dev", "test", "all"], default="test")
    args = parser.parse_args()
    manifest = verify_manifest(args.corpus)
    cases = [{**case, "diff": (args.corpus / "cases" / case["id"] / "review.diff").read_text(encoding="utf-8")}
             for case in manifest["cases"] if args.split == "all" or case["split"] == args.split]
    data = json.loads(args.results.read_bytes())
    results = data["results"]
    all_ids = {case["id"] for case in manifest["cases"]}
    returned_ids = [record["case"] for record in results]
    if len(returned_ids) != len(set(returned_ids)) or not set(returned_ids) <= all_ids:
        raise ValueError("Unknown or duplicate exported case")
    ids = {case["id"] for case in cases}
    report = score_results(cases, [r for r in results if r["case"] in ids])
    report["arm"] = data["arm"]
    report["split"] = args.split
    args.output.mkdir(parents=True, exist_ok=True)
    sheet, mapping = blind_sheet(report)
    for name, value in [("scores.json", report), ("blind-adjudication-v1.json", sheet), ("adjudication-mapping-v1.json", mapping)]:
        (args.output / name).write_bytes(canonical(value))
    print(json.dumps({"arm": data["arm"], "cases": len(cases), "TP": report["true_positives"], "FP": report["false_positives_count"], "misses": len(report["misses"])}))


if __name__ == "__main__":
    main()
