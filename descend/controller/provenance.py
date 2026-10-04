"""Hash real local bytes and report unavailable provider identities honestly."""
from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import subprocess
import sys
from pathlib import Path

from descend.registry import canonical_hash

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def byte_hash(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def source_hash(*directories):
    files = {}
    for directory in directories:
        path = PROJECT_ROOT / directory
        paths = [path] if path.is_file() else sorted(path.rglob("*.py"))
        for item in paths:
            files[item.relative_to(PROJECT_ROOT).as_posix()] = byte_hash(item)
    return canonical_hash(files)


def runtime_record():
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=PROJECT_ROOT, text=True).strip()
    return {"git_sha": git("rev-parse", "HEAD"), "worktree_dirty": bool(git("status", "--porcelain")),
            "python": sys.version, "platform": platform.platform(),
            "dependency_lock_hash": byte_hash(PROJECT_ROOT / "requirements-lock.txt"),
            "installed_packages": {name: importlib.metadata.version(name) for name in
                                   ("PyYAML", "jsonschema", "openai", "tokenizers")},
            "controller_code_hash": source_hash("descend/controller", "descend/sandbox", "descend/tools"),
            "evaluator_code_hash": source_hash("descend/evaluation", "descend/dsl", "descend/controller/controller.py"),
            "dsl_generator_hash": source_hash("descend/dsl"),
            "provider_weight_hash": None, "provider_weight_hash_reason": "Provider weights are not exposed"}
