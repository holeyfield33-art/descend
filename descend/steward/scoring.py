"""Predeclared v1 automatic scoring; no execution, prompts or provider calls."""
from __future__ import annotations

import hashlib
import json
import math
import statistics

from descend.steward.findings import validate_findings


def wilson(successes: int, total: int) -> dict:
    if type(successes) is not int or type(total) is not int or not 0 <= successes <= total:
        raise ValueError("Invalid proportion counts")
    if total == 0:
        return {"numerator": successes, "denominator": total, "rate": None, "wilson95": None}
    z = 1.959963984540054
    p = successes / total
    scale = 1 + z*z/total
    center = (p + z*z/(2*total)) / scale
    radius = z * math.sqrt(p*(1-p)/total + z*z/(4*total*total)) / scale
    return {"numerator": successes, "denominator": total, "rate": p,
            "wilson95": [max(0, center-radius), min(1, center+radius)]}


def score_results(cases: list[dict], results: list[dict], tolerance: int = 2) -> dict:
    if type(tolerance) is not int or tolerance < 0:
        raise ValueError("Invalid location tolerance")
    case_ids = {case["id"] for case in cases}
    if len(case_ids) != len(cases):
        raise ValueError("Duplicate case IDs")
    indexed = {}
    for result in results:
        if result["case"] not in case_ids or result["case"] in indexed:
            raise ValueError("Unknown or duplicate result case")
        indexed[result["case"]] = result
    raw_count = valid_count = tp = fp = 0
    found_bugs, clean_alarms, decoy_alarms = set(), set(), set()
    misses, false_positives, errors, classifications = [], [], [], []
    for case in cases:
        record = indexed.get(case["id"], {})
        if not record or record.get("error"):
            errors.append({"case": case["id"], "error": record.get("error", "missing_result")})
        content = record.get("content", '{"findings": []}')
        try:
            parsed = json.loads(content)
            submitted = parsed.get("findings") if isinstance(parsed, dict) else None
        except (ValueError, TypeError):
            submitted = None
        if not isinstance(submitted, list):
            errors.append({"case": case["id"], "error": "invalid_response_schema"})
            submitted = []
        raw_count += len(submitted)
        validated = validate_findings(content, case["diff"], case.get("paths", ["app.py"]))
        if record.get("error"):
            # An errored provider attempt cannot earn recall from partial output.
            validated = {"findings": []}
        valid_count += len(validated["findings"])
        seen = set()
        for finding in validated["findings"]:
            key = (finding["path"], finding["line"], finding["evidence"].strip())
            if key in seen:
                continue
            seen.add(key)
            truth = case.get("ground_truth")
            match = (case["label"] == "bug" and truth and finding["path"] == truth["path"]
                     and truth["start"]-tolerance <= finding["line"] <= truth["end"]+tolerance)
            identity = hashlib.sha256(json.dumps([case["id"], *key], ensure_ascii=False).encode()).hexdigest()[:24]
            row = {"id": identity, "case": case["id"], "finding": finding,
                   "automatic": "TP" if match else "FP"}
            classifications.append(row)
            if match:
                tp += 1
                found_bugs.add(case["id"])
            else:
                fp += 1
                false_positives.append(row)
                if case["label"] == "clean":
                    clean_alarms.add(case["id"])
                elif case["label"] == "decoy":
                    decoy_alarms.add(case["id"])
        if case["label"] == "bug" and case["id"] not in found_bugs:
            misses.append(case["id"])
    latency = [r["latency_seconds"] for r in results if type(r.get("latency_seconds")) in (int, float) and r["latency_seconds"] >= 0]
    costs = [r["accounted_upper_bound_usd"] for r in results if type(r.get("accounted_upper_bound_usd")) in (int, float) and r["accounted_upper_bound_usd"] >= 0]
    usage = [r["usage"] for r in results if isinstance(r.get("usage"), dict) and all(type(r["usage"].get(k)) is int and r["usage"][k] >= 0 for k in ("prompt_tokens", "completion_tokens"))]
    return {"metric_version": "v1", "location_tolerance": tolerance, "cases": len(cases),
            "latency_seconds": {"observed_cases": len(latency), "median": statistics.median(latency) if latency else None},
            "cost_usd": {"observed_cases": len(costs), "total": sum(costs) if costs else None},
            "provider_usage": {"observed_cases": len(usage), "prompt_tokens": sum(r["prompt_tokens"] for r in usage) if usage else None,
                               "completion_tokens": sum(r["completion_tokens"] for r in usage) if usage else None},
            "citation_valid": wilson(valid_count, raw_count), "true_positives": tp, "false_positives_count": fp,
            "precision": wilson(tp, tp+fp),
            "recall": wilson(len(found_bugs), sum(c["label"] == "bug" for c in cases)),
            "clean_false_alarm": wilson(len(clean_alarms), sum(c["label"] == "clean" for c in cases)),
            "decoy_false_alarm": wilson(len(decoy_alarms), sum(c["label"] == "decoy" for c in cases)),
            "misses": misses, "false_positives": false_positives, "errors": errors,
            "classifications": classifications, "verification": None, "adjudicated": None,
            "limitation": "Small seeded sample; location matching is weak; correlated families are not independent trials."}


def blind_sheet(scores: dict) -> tuple[list[dict], list[dict]]:
    sheet, mapping = [], []
    for row in scores["classifications"]:
        finding = row["finding"]
        # Identity does not encode a human-readable case/model/label.
        sheet.append({"id": row["id"], "explanation": finding["reason"], "snippet": finding["evidence"], "decision": None})
        mapping.append({"id": row["id"], "case": row["case"], "automatic": row["automatic"]})
    sheet.sort(key=lambda row: row["id"])
    return sheet, mapping
