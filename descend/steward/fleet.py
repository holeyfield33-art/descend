"""Explicit multi-repository watch configuration; no implicit workspace discovery."""
from __future__ import annotations

import json
from pathlib import Path


def load_fleet(path: str | Path) -> list[dict]:
    config = Path(path).resolve(strict=True)
    data = json.loads(config.read_text(encoding="utf-8"))
    rows = data.get("repositories") if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        raise ValueError("Configuration needs a nonempty repositories list")
    result, seen = [], set()
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or set(row) - {"path", "mode", "interval_seconds", "vibe_report", "asi_catalog"}:
            raise ValueError(f"Invalid repository entry {index}")
        if not isinstance(row.get("path"), str) or not row["path"].strip():
            raise ValueError(f"Repository {index} needs a path")
        repo = Path(row["path"])
        if not repo.is_absolute():
            repo = config.parent / repo
        repo = repo.resolve(strict=True)
        if not repo.is_dir() or repo in seen:
            raise ValueError(f"Repository {index} is duplicated or not a directory")
        seen.add(repo)
        mode = row.get("mode", "mock")
        interval = row.get("interval_seconds", 60)
        if mode not in ("mock", "live") or type(interval) is not int or interval < 10:
            raise ValueError(f"Invalid mode or interval for repository {index}")
        vibe, asi = row.get("vibe_report"), row.get("asi_catalog")
        if bool(vibe) != bool(asi) or (vibe and mode != "live"):
            raise ValueError(f"Vibe/ASI paths must be paired on a live repository {index}")
        def resolve_optional(value):
            if value is None:
                return None
            if not isinstance(value, str):
                raise ValueError(f"Invalid context path for repository {index}")
            selected = Path(value)
            return (selected if selected.is_absolute() else config.parent / selected).resolve(strict=True)
        result.append({"path": repo, "mode": mode, "interval_seconds": interval,
                       "vibe_report": resolve_optional(vibe), "asi_catalog": resolve_optional(asi)})
    return result
