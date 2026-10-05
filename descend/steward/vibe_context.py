"""Pin and summarize an offline Vibe/ASI report without forwarding source excerpts."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def load_vibe_context(report_path: str | Path, catalog_path: str | Path, *, commit: str) -> dict:
    raw = Path(report_path).read_bytes()
    report = json.loads(raw)
    meta = report.get("metadata") or {}
    scope = meta.get("scan_scope") or {}
    if meta.get("schema_version") != "2.0":
        raise ValueError("Unsupported Vibe report schema")
    revision = meta.get("repository_revision") or {}
    if revision.get("commit") != commit or revision.get("dirty") is not False:
        raise ValueError("Vibe report does not match a clean reviewed commit")
    if scope.get("inventory_complete") is not True or scope.get("budget_exhausted_reason"):
        raise ValueError("Vibe report inventory is incomplete")
    if meta.get("assessment_completeness") == "PARTIAL":
        raise ValueError("Partial Vibe report cannot supply review context")
    catalog_file = Path(catalog_path)
    if not catalog_file.is_file():
        raise ValueError("Provide the exact ASI catalog JSON file, not a directory")
    # Vibe's local-catalog identity hashes filename, NUL, bytes, NUL.
    catalog_hash = hashlib.sha256()
    catalog_hash.update(catalog_file.name.encode("utf-8"))
    catalog_hash.update(b"\0")
    catalog_hash.update(catalog_file.read_bytes())
    catalog_hash.update(b"\0")
    expected = "sha256:" + catalog_hash.hexdigest()
    asi = meta.get("asi_catalog") or {}
    if asi.get("supplied") is not True or asi.get("source_hash") != expected:
        raise ValueError("Vibe report does not match the selected ASI catalog")
    risks = report.get("risks") or {}
    scenarios = risks.get("scenarios") or []
    matrix = report.get("asi_matrix") or {}
    summary = matrix.get("summary") or {}
    # Only bounded IDs, titles and status counts enter the provider prompt.
    leads = []
    for item in scenarios[:5]:
        if isinstance(item, dict):
            leads.append({"id": str(item.get("risk_id", ""))[:80],
                          "title": str(item.get("title", ""))[:120],
                          "reachability": str(item.get("reachability_status", ""))[:40]})
    return {"tool": "vibe-explainer", "schema": "2.0", "commit": commit,
            "report_sha256": hashlib.sha256(raw).hexdigest(), "asi_catalog_sha256": expected,
            "asi_version": str(asi.get("version", ""))[:40],
            "static_leads": leads,
            "asi_applicable_classes": int(summary.get("applicable", 0)),
            "asi_class_evidence_observed": int(summary.get("class_evidence_observed", 0)),
            "limitation": "Offline static leads and taxonomy relevance only; not vulnerability or control-effectiveness findings."}
