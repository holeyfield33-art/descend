import json

from descend.steward.findings import added_lines, validate_findings


DIFF = """diff --git a/app.py b/app.py
index 1..2 100644
--- a/app.py
+++ b/app.py
@@ -1,3 +1,4 @@
 def total(items):
-    return sum(items)
+    return sum(items[:-1])
+# explanatory comment
 pass
"""


def _finding(**overrides):
    item = {"path": "app.py", "line": 2, "evidence": "    return sum(items[:-1])",
            "severity": "medium", "reason": "Last element omitted", "verification": "Check [1,2,3]"}
    item.update(overrides)
    return item


def test_added_line_mapping_and_valid_citation():
    assert added_lines(DIFF)[("app.py", 2)] == "    return sum(items[:-1])"
    parsed = validate_findings(json.dumps({"findings": [_finding()]}), DIFF, ["app.py"])
    assert len(parsed["findings"]) == 1
    assert parsed["rejected"] == []


def test_rejects_fabricated_and_context_citations():
    items = [_finding(line=1, evidence="def total(items):"),
             _finding(evidence="return sum(items)"), _finding(path="secret.py"),
             _finding(line=True)]
    parsed = validate_findings(json.dumps({"findings": items}), DIFF, ["app.py"])
    assert parsed["findings"] == []
    assert len(parsed["rejected"]) == len(items)


def test_malformed_output_is_visible_without_findings():
    parsed = validate_findings("Here is my answer", DIFF, ["app.py"])
    assert parsed["findings"] == []
    assert parsed["parse_error"]


def test_unique_added_evidence_repairs_wrong_line_without_skipping_schema_checks():
    parsed = validate_findings(json.dumps({"findings": [_finding(line=99)]}), DIFF, ["app.py"])
    assert parsed["findings"][0]["line"] == 2
    assert parsed["findings"][0]["reported_line"] == 99
    assert parsed["findings"][0]["line_corrected"] is True
    invalid = validate_findings(json.dumps({"findings": [_finding(line=99, severity="critical")]}),
                                DIFF, ["app.py"])
    assert invalid["findings"] == []


def test_ambiguous_evidence_does_not_repair_line():
    repeated = DIFF + "@@ -10,0 +20,1 @@\n+    return sum(items[:-1])\n"
    parsed = validate_findings(json.dumps({"findings": [_finding(line=99)]}), repeated, ["app.py"])
    assert parsed["findings"] == []
