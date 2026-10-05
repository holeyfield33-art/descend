"""Commit watcher: snapshot an allowlisted Git checkout and store one review per commit."""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

CODE_EXTENSIONS = frozenset({".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs"})
SECRET_PATH = re.compile(r"(^|/)(\.env(?:\..*)?|[^/]*(?:secret|credential|private.?key)[^/]*)$", re.I)
SECRET_LINE = re.compile(r"(?i)(api[_-]?key|access[_-]?token|password|private[_-]?key)\s*[=:]\s*['\"]?[^\s'\"]{8,}")
MAX_DIFF_BYTES = 12_000
GIT_EXECUTABLE = shutil.which("git")


def git_environment() -> dict[str, str]:
    """Controller-owned Git environment; never inherit credentials or Git overrides."""
    env = {"PATH": os.defpath, "LANG": "C", "LC_ALL": "C",
           "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
           "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1",
           "GIT_OPTIONAL_LOCKS": "0", "GIT_LITERAL_PATHSPECS": "1"}
    if os.name == "nt":
        # Windows process startup requires SystemRoot; no arbitrary inherited keys.
        env["SystemRoot"] = os.environ.get("SystemRoot", r"C:\Windows")
    return env


def _git(repo: Path, *args: str) -> bytes:
    if GIT_EXECUTABLE is None:
        raise RuntimeError("Git executable unavailable")
    return subprocess.run([GIT_EXECUTABLE, "--no-pager", "--no-replace-objects",
                           "-c", "core.fsmonitor=false", "-c", "core.hooksPath=" + os.devnull,
                           "-c", "protocol.allow=never", "-c", "submodule.recurse=false",
                           "-C", str(repo), *args], check=True, capture_output=True,
                          timeout=20, env=git_environment()).stdout


def commit_snapshot(repo: str | Path) -> dict:
    root = Path(repo).resolve(strict=True)
    top = Path(_git(root, "rev-parse", "--show-toplevel").decode().strip()).resolve()
    if top != root:
        raise ValueError("Watch path must be the Git checkout root")
    sha = _git(root, "rev-parse", "HEAD").decode().strip()
    lineage = _git(root, "rev-list", "--parents", "-n", "1", "HEAD").decode().split()
    parent = lineage[1] if len(lineage) > 1 else None
    if parent:
        names = _git(root, "diff", "--name-only", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", parent, sha).decode().splitlines()
    else:
        names = _git(root, "diff-tree", "--no-commit-id", "--name-only", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", "-r", "--root", sha).decode().splitlines()
    if any(SECRET_PATH.search(name.replace("\\", "/")) for name in names):
        return {"repo": str(root), "sha": sha, "status": "skipped_sensitive_path", "paths": names}
    selected = [name for name in names if Path(name).suffix.lower() in CODE_EXTENSIONS]
    if not selected:
        return {"repo": str(root), "sha": sha, "status": "skipped_no_code", "paths": names}
    if parent:
        raw = _git(root, "diff", "--patch", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", "--no-renames", parent, sha, "--", *selected)
    else:
        raw = _git(root, "show", "--format=", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", "--no-renames", sha, "--", *selected)
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
            db.execute("CREATE TABLE IF NOT EXISTS decisions (repo TEXT NOT NULL, sha TEXT NOT NULL, "
                       "finding_index INTEGER NOT NULL, decision TEXT NOT NULL, note TEXT NOT NULL, "
                       "decided_at TEXT NOT NULL, PRIMARY KEY(repo, sha, finding_index))")

    def get(self, repo: str, sha: str) -> dict | None:
        with sqlite3.connect(self.path) as db:
            row = db.execute("SELECT payload FROM reviews WHERE repo=? AND sha=?", (repo, sha)).fetchone()
        return json.loads(row[0]) if row else None

    def claim(self, snapshot: dict) -> bool:
        pending = {key: value for key, value in snapshot.items() if key != "diff"}
        pending["status"] = "in_progress"
        with sqlite3.connect(self.path) as db:
            cursor = db.execute("INSERT OR IGNORE INTO reviews VALUES (?,?,?,?,?)",
                                (pending["repo"], pending["sha"], datetime.now(timezone.utc).isoformat(),
                                 pending["status"], json.dumps(pending, ensure_ascii=False)))
        return cursor.rowcount == 1

    def update(self, result: dict) -> None:
        with sqlite3.connect(self.path) as db:
            db.execute("UPDATE reviews SET status=?,payload=? WHERE repo=? AND sha=?",
                       (result["status"], json.dumps(result, ensure_ascii=False),
                        result["repo"], result["sha"]))

    def recent(self, limit: int = 50) -> list[dict]:
        if type(limit) is not int or not 1 <= limit <= 200:
            raise ValueError("Invalid review limit")
        with sqlite3.connect(self.path) as db:
            rows = db.execute("SELECT payload FROM reviews ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()
            decisions = db.execute("SELECT repo,sha,finding_index,decision,note,decided_at FROM decisions").fetchall()
        indexed = {}
        for repo, sha, index, decision, note, decided_at in decisions:
            indexed.setdefault((repo, sha), {})[index] = {"decision": decision, "note": note,
                                                          "decided_at": decided_at}
        results = [json.loads(row[0]) for row in rows]
        for result in results:
            result["decisions"] = indexed.get((result["repo"], result["sha"]), {})
        return results

    def decide(self, repo: str, sha: str, finding_index: int, decision: str, note: str = "") -> dict:
        if decision not in ("confirmed", "dismissed"):
            raise ValueError("Decision must be confirmed or dismissed")
        if type(finding_index) is not int or finding_index < 0:
            raise ValueError("Invalid finding index")
        if not isinstance(note, str) or len(note) > 1000:
            raise ValueError("Invalid note")
        review = self.get(repo, sha)
        findings = (review or {}).get("review", {}).get("findings", [])
        if finding_index >= len(findings):
            raise ValueError("Finding does not exist or lacks validated citation")
        at = datetime.now(timezone.utc).isoformat()
        with sqlite3.connect(self.path) as db:
            db.execute("INSERT INTO decisions VALUES (?,?,?,?,?,?) ON CONFLICT(repo,sha,finding_index) "
                       "DO UPDATE SET decision=excluded.decision,note=excluded.note,decided_at=excluded.decided_at",
                       (repo, sha, finding_index, decision, note, at))
        return {"repo": repo, "sha": sha, "finding_index": finding_index,
                "decision": decision, "note": note, "decided_at": at}


def scan_once(repo: str | Path, store: ReviewStore, reviewer: Callable[[dict], dict]) -> dict:
    snapshot = commit_snapshot(repo)
    existing = store.get(snapshot["repo"], snapshot["sha"])
    if existing is not None:
        review = existing.get("review") or {}
        if snapshot["status"] == "ready" and review.get("protocol_version") == 2:
            from descend.steward.findings import validate_findings
            refreshed = validate_findings(review.get("content", ""), snapshot["diff"], snapshot["paths"])
            if any(review.get(key) != value for key, value in refreshed.items()):
                review.update(refreshed)
                store.update(existing)
        return {**existing, "cached": True}
    if not store.claim(snapshot):
        return {**store.get(snapshot["repo"], snapshot["sha"]), "cached": True}
    result = {key: value for key, value in snapshot.items() if key != "diff"}
    if snapshot["status"] == "ready":
        try:
            result["review"] = reviewer(snapshot)
            result["status"] = "reviewed"
        except Exception as exc:
            # Never auto-retry an ambiguous paid call after a crash or error.
            result["status"] = "error"
            result["error_type"] = type(exc).__name__
            store.update(result)
            raise
    store.update(result)
    return result
