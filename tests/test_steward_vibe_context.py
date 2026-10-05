import hashlib
import json

import pytest

from descend.steward.vibe_context import load_vibe_context


def test_vibe_context_requires_matching_commit_and_catalog(tmp_path):
    catalog = tmp_path / "asi-catalog.json"
    catalog.write_text('{"classes": []}', encoding="utf-8")
    digest = hashlib.sha256(catalog.name.encode() + b"\0" + catalog.read_bytes() + b"\0").hexdigest()
    report = tmp_path / "report.json"
    payload = {"metadata": {"schema_version": "2.0", "repository_revision": {"commit": "a" * 40,
               "dirty": False}, "scan_scope": {"inventory_complete": True,
               "budget_exhausted_reason": None}, "assessment_completeness": "AGGREGATED",
               "asi_catalog": {"supplied": True, "source_hash": "sha256:" + digest,
                               "version": "0.2.0-draft"}},
               "risks": {"scenarios": [{"risk_id": "R1", "title": "Static concern",
                                        "reachability_status": "NOT_ESTABLISHED"}]},
               "asi_matrix": {"summary": {"applicable": 2, "class_evidence_observed": 0}}}
    report.write_text(json.dumps(payload), encoding="utf-8")
    context = load_vibe_context(report, catalog, commit="a" * 40)
    assert context["static_leads"][0]["title"] == "Static concern"
    assert context["asi_class_evidence_observed"] == 0
    with pytest.raises(ValueError, match="clean reviewed commit"):
        load_vibe_context(report, catalog, commit="b" * 40)
    catalog.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError, match="ASI catalog"):
        load_vibe_context(report, catalog, commit="a" * 40)
