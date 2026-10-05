"""Validate model citations against added lines in the exact reviewed Git diff."""
from __future__ import annotations

import json
import re

HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")
SEVERITIES = frozenset({"low", "medium", "high"})


def added_lines(diff: str) -> dict[tuple[str, int], str]:
    added: dict[tuple[str, int], str] = {}
    path: str | None = None
    line: int | None = None
    for row in diff.splitlines():
        if row.startswith("+++ "):
            path = row[6:] if row.startswith("+++ b/") else None
            line = None
        elif row.startswith("@@ "):
            match = HUNK.match(row)
            line = int(match.group(1)) if match else None
        elif line is not None and path is not None:
            if row.startswith("+"):
                added[(path, line)] = row[1:]
                line += 1
            elif row.startswith(" "):
                line += 1
            elif row.startswith("-") or row.startswith("\\"):
                pass
            else:
                line = None
    return added


def validate_findings(content: str, diff: str, paths: list[str]) -> dict:
    try:
        data = json.loads(content)
    except (ValueError, TypeError):
        return {"findings": [], "rejected": [], "parse_error": "Response was not JSON"}
    if not isinstance(data, dict) or not isinstance(data.get("findings"), list):
        return {"findings": [], "rejected": [], "parse_error": "Expected a findings array"}
    additions = added_lines(diff)
    accepted, rejected = [], []
    for index, item in enumerate(data["findings"][:20]):
        reason = None
        if not isinstance(item, dict):
            reason = "Finding is not an object"
        else:
            path, line, evidence = item.get("path"), item.get("line"), item.get("evidence")
            if (not isinstance(path, str) or path not in paths or type(line) is not int
                    or line < 1 or not isinstance(evidence, str) or not evidence.strip()):
                reason = "Invalid path, line or evidence"
            elif additions.get((path, line), "").strip() != evidence.strip():
                matches = [number for (candidate_path, number), source in additions.items()
                           if candidate_path == path and source.strip() == evidence.strip()]
                if len(matches) == 1:
                    item = {**item, "reported_line": line, "line": matches[0], "line_corrected": True}
                else:
                    reason = "Evidence does not uniquely match an added line"
            if reason is None:
                if item.get("severity") not in SEVERITIES:
                    reason = "Invalid severity"
                elif not isinstance(item.get("reason"), str) or not item["reason"].strip():
                    reason = "Missing reason"
                elif not isinstance(item.get("verification"), str) or not item["verification"].strip():
                    reason = "Missing verification idea"
        if reason:
            rejected.append({"index": index, "reason": reason})
        else:
            accepted.append({key: item[key] for key in
                             ("path", "line", "evidence", "severity", "reason", "verification")})
            if item.get("line_corrected"):
                accepted[-1].update(reported_line=item["reported_line"], line_corrected=True)
    if len(data["findings"]) > 20:
        rejected.append({"index": 20, "reason": "More than 20 findings"})
    return {"findings": accepted, "rejected": rejected, "parse_error": None}
