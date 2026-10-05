"""Commit watcher: snapshot an allowlisted Git checkout and store one review per commit."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

CODE_EXTENSIONS = frozenset({".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"})
SECRET_PATH = re.compile(r"(^|/)(\.env(?:\..*)?|[^/]*(?:secret|credential|private.?key)[^/]*)$", re.I)
SECRET_LINE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|password|private[_-]?key)\s*[=:]\s*['\"]?[^\s'\"]{8,}")
MAX_DIFF_BYTES = 12_000


def _git(repo: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          timeout=20).stdout


def commit_snapshot(repo: str | Path) -> dict:
    root = Path(repo).resolve(strict=True)
    top = Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root:
        raise ValueError("Watch path must be the Git checkout root")
    sha = _git(root, "rev-parse", "HEAD").decode().strip()
    lineage = _git(root, "rev-list", "--parents", "-n", "1", "HEAD").decode().split()
    parent = lineage[1] if len(lineage) > 1 else None
    if parent:
        names = _git(root, "diff", "--name-only", "--no-ext-diff", parent, sha).decode().splitlines()
    else:
        names = _git(root, "diff-tree", "--no-commit-id", "--name-only", "-r", "--root", sha).decode().splitlines()
    if any(SECRET_PATH.search(name.replace("\\", "/")) for name in names):
        return {"repo": str(root), "sha": sha, "status": "skipped_sensitive_path", "paths": names}
    selected = [name for name in names if Path(name).suffix.lower() in CODE_EXTENSIONS]
    if not selected:
        return {"repo": str(root), "sha": sha, "status": "skipped_no_code", "paths": names}
    if parent:
        raw = _git(root, "diff", "--patch", "--no-ext-diff", "--no-renames", parent, sha, "--", *selected)
    else:
        raw = _git(root, "show", "--format=", "--no-ext-diff", "--no-renames", sha, "--", *selected)
    if len(raw) > MAX_DIFF_BYTES:
        return {"repo": str(root), "sha": sha, "status": "skipped_large_diff", "paths": selected}
    diff = raw.decode("utf-8", errors="replace")
    if SECRET_LINE.search(diff):
        return {"repo": str(root), "sha": sha, "status": "skipped_sensitive_content", "paths": selected}
    return {"repo": str(root), "sha": sha, "status": "ready", "paths": selected,
            "diff": diff, "diff_sha256": hashlib.sha256(raw).hexdigest()}


class ReviewStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.path) as db:
            db.execute("CREATE TABLE IF NOT EXISTS reviews (repo TEXT NOT NULL, sha TEXT NOT NULL, "
                       "created_at TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, "
                       "PRIMARY KEY(repo, sha))")

    def get(self, repo: str, sha: str) -> dict | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM reviews WHERE repo=? AND sha=?", (repo, sha)).fetchone()
        return json.loads(row[0]) if row else None

    def save(self, result: dict) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?)",
                       (result["repo"], result["sha"], datetime.now(timezone.utc).isoformat(),
                        result["status"], json.dumps(result, ensure_ascii=False)))


def scan_once(repo: str | Path, store: ReviewStore, reviewer: Callable[[dict], dict]) -> dict:
    snapshot = commit_snapshot(repo)
    existing = store.get(snapshot["repo"], snapshot["sha"])
    if existing is not None:
        return {**existing, "cached": True}
    result = {key: value for key, value in snapshot.items() if key != "diff"}
    if snapshot["status"] == "ready":
        result["review"] = reviewer(snapshot)
        result["status"] = "reviewed"
    store.save(result)
    return result
