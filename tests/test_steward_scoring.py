import json

import pytest

from descend.steward.scoring import blind_sheet, score_results, wilson


def case(id="bug", label="bug"):
    return {"id": id, "label": label, "ground_truth": {"path": "app.py", "start": 1, "end": 1},
            "diff": "--- a/app.py\n+++ b/app.py\n@@ -0,0 +1,5 @@\n+bad = 1\n+x = 2\n+y = 3\n+z = 4\n+other = 5\n"}


def finding(line=1, evidence="bad = 1", path="app.py"):
    return dict(path=path, line=line, evidence=evidence, severity="low", reason="canned claim", verification="check")


def result(id, findings):
    return {"case": id, "content": json.dumps({"findings": findings})}


def test_duplicates_wrong_locations_and_clean_false_alarms():
    cases = [case(), case("clean", "clean"), case("decoy", "decoy"), case("miss")]
    results = [result("bug", [finding(), finding(), finding(5, "other = 5"), finding(path="wrong.py")]),
               result("clean", [finding(), finding(2, "x = 2")]), result("decoy", [finding()])]
    score = score_results(cases, results)
    assert score["true_positives"] == 1
    assert score["false_positives_count"] == 4
    assert score["citation_valid"]["numerator"] == 6
    assert score["citation_valid"]["denominator"] == 7
    assert score["recall"]["rate"] == 0.5
    assert score["precision"]["rate"] == 0.2
    assert score["clean_false_alarm"]["rate"] == 1
    assert score["misses"] == ["miss"]
    sheet, mapping = blind_sheet(score)
    assert len(sheet) == len(mapping) == 5
    assert all(set(row) == {"id", "explanation", "snippet", "decision"} for row in sheet)


def test_noop_errors_and_undefined_precision():
    score = score_results([case()], [{"case": "bug", "content": "malformed", "error": "provider_error"}])
    assert score["precision"]["rate"] is None
    assert score["recall"]["rate"] == 0
    assert score["verification"] is None
    assert len(score["errors"]) == 2
    with pytest.raises(ValueError, match="duplicate"):
        score_results([case()], [result("bug", []), result("bug", [])])
    partial = result("bug", [finding()])
    partial["error"] = "provider_error"
    assert score_results([case()], [partial])["recall"]["rate"] == 0


def test_wilson_known_interval_and_invalid_counts():
    assert wilson(5, 10)["wilson95"] == pytest.approx([0.2365930905, 0.7634069095])
    assert wilson(0, 0)["wilson95"] is None
    with pytest.raises(ValueError):
        wilson(2, 1)
