"""Export-only verification for a deliberately narrow Python function grammar."""
from __future__ import annotations

import ast
import difflib
import hashlib
import json
import re
import shutil
import sqlite3
from contextlib import closing
import tempfile
from pathlib import Path

from descend.steward.act_worker import run_tests
from descend.steward.corpus import canonical
from descend.steward.findings import validate_findings

MAX_PROPOSAL_BYTES = 24000
MAX_TEST_BYTES = 8000
MAX_SOURCE_BYTES = 12000
FAILURES = {"AssertionError", "IndexError", "KeyError", "ValueError", "TypeError", "UnicodeDecodeError"}
CALLS = {"solve", "StringIO", "sum", "max", "min", "sorted", "len", "int", "float", "str", "abs", "round", "list", "dict", "tuple", "bool", "range", "enumerate", "zip", "callable"}
METHODS = {"get", "sort", "read", "close", "decode", "encode", "append", "copy", "items", "values", "keys"}
NODES = {ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return, ast.Expr,
         ast.Call, ast.Name, ast.Load, ast.Store, ast.Constant, ast.BinOp, ast.UnaryOp,
         ast.BoolOp, ast.Compare, ast.Assign, ast.AugAssign, ast.Dict, ast.List,
         ast.Tuple, ast.Subscript, ast.Slice, ast.Attribute, ast.Assert, ast.IfExp,
         ast.Try, ast.ExceptHandler, ast.Pass, ast.ImportFrom, ast.alias, ast.keyword,
         ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
         ast.USub, ast.UAdd, ast.Not, ast.And, ast.Or, ast.Eq, ast.NotEq,
         ast.Lt, ast.LtE, ast.Gt, ast.GtE, ast.Is, ast.IsNot, ast.In, ast.NotIn}


class ProposalRejected(ValueError):
    pass


def source_hash(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def validate_source(source: str, *, test: bool, test_function: str = "test_reproducer") -> None:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError, RecursionError):
        raise ProposalRejected("Invalid Python syntax") from None
    functions = [node for node in tree.body if isinstance(node, ast.FunctionDef)]
    expected = test_function if test else "solve"
    if len(functions) != 1 or functions[0].name != expected or sum(isinstance(n, ast.FunctionDef) for n in ast.walk(tree)) != 1:
        raise ProposalRejected("Only the supported single function is allowed")
    if any(not isinstance(node, (ast.FunctionDef, ast.ImportFrom)) for node in tree.body):
        raise ProposalRejected("Top-level executable statements rejected")
    if test and (functions[0].args.args or not any(isinstance(n, ast.Assert) for n in ast.walk(functions[0]))):
        raise ProposalRejected("Reproducer must be an assertion test without fixtures")
    if not test and ([a.arg for a in functions[0].args.args] != ["values"]):
        raise ProposalRejected("Unsupported target function signature")
    for node in ast.walk(tree):
        if type(node) not in NODES:
            raise ProposalRejected("Unsupported Python construct")
        if isinstance(node, ast.FunctionDef) and (node.decorator_list or node.returns or node.args.defaults or node.args.kwonlyargs or node.args.vararg or node.args.kwarg):
            raise ProposalRejected("Decorators/defaults/annotations rejected")
        if isinstance(node, ast.arg) and node.annotation is not None:
            raise ProposalRejected("Argument annotations rejected")
        if isinstance(node, ast.Name) and (node.id.startswith("_") or node.id in {"pytest", "globals", "locals", "vars", "getattr", "setattr", "eval", "exec", "compile", "open", "type", "object", "super", "print", "input", "exit", "quit"}):
            raise ProposalRejected("Privileged or dynamic name rejected")
        if isinstance(node, ast.Attribute) and (node.attr.startswith("_") or node.attr not in METHODS | {"closed"}):
            raise ProposalRejected("Unsupported attribute")
        if isinstance(node, ast.Call):
            if not ((isinstance(node.func, ast.Name) and node.func.id in CALLS) or
                    (isinstance(node.func, ast.Attribute) and node.func.attr in METHODS)):
                raise ProposalRejected("Unsupported call")
        if isinstance(node, ast.ImportFrom):
            allowed = {("app", "solve"), ("io", "StringIO")} if test else set()
            if node.level or any(alias.asname or (node.module, alias.name) not in allowed for alias in node.names):
                raise ProposalRejected("Import rejected")
        if test and isinstance(node, (ast.Try, ast.Return, ast.Pass, ast.IfExp)):
            raise ProposalRejected("Test control flow could suppress assertions")
        if isinstance(node, ast.Assign) and any(not isinstance(target, (ast.Name, ast.Subscript)) for target in node.targets):
            raise ProposalRejected("Attribute assignment rejected")
        if isinstance(node, ast.AugAssign) and not isinstance(node.target, (ast.Name, ast.Subscript)):
            raise ProposalRejected("Attribute mutation rejected")


def validate_proposal(raw: str, finding: dict) -> dict:
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_PROPOSAL_BYTES:
        raise ProposalRejected("Proposal byte cap exceeded")
    try:
        proposal = json.loads(raw)
    except (ValueError, TypeError, RecursionError):
        raise ProposalRejected("Proposal is not JSON") from None
    if not isinstance(proposal, dict) or set(proposal) != {"path", "test_source", "replacement_source", "expected_failure"}:
        raise ProposalRejected("Unexpected proposal schema")
    if proposal["path"] != "app.py" or finding.get("path") != "app.py":
        raise ProposalRejected("Initial act scope allows cited app.py only")
    test = proposal["test_source"]
    replacement = proposal["replacement_source"]
    if not isinstance(test, str) or len(test.encode()) > MAX_TEST_BYTES:
        raise ProposalRejected("Test byte cap exceeded")
    if not isinstance(proposal["expected_failure"], str) or proposal["expected_failure"] not in FAILURES:
        raise ProposalRejected("Unsupported failure class")
    validate_source(test, test=True)
    if replacement is not None:
        if not isinstance(replacement, str) or len(replacement.encode()) > MAX_SOURCE_BYTES:
            raise ProposalRejected("Patch source byte cap exceeded")
        validate_source(replacement, test=False)
    return proposal


class ActStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        with closing(sqlite3.connect(path)) as db, db:
            db.execute("CREATE TABLE IF NOT EXISTS acts (repo TEXT, sha TEXT, finding INTEGER, status TEXT, payload TEXT, PRIMARY KEY(repo,sha,finding))")

    def claim(self, repo: str, sha: str, finding: int, *, commit_cap: int = 1) -> bool:
        if type(commit_cap) is not int or commit_cap < 0 or type(finding) is not int or finding < 0:
            raise ValueError("Invalid action budget")
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("BEGIN IMMEDIATE")
            count = db.execute("SELECT COUNT(*) FROM acts WHERE repo=? AND sha=?", (repo, sha)).fetchone()[0]
            if count >= commit_cap:
                return False
            cursor = db.execute("INSERT OR IGNORE INTO acts VALUES (?,?,?,'in_progress','{}')", (repo, sha, finding))
            return cursor.rowcount == 1

    def finish(self, repo: str, sha: str, finding: int, evidence: dict):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute("UPDATE acts SET status=?,payload=? WHERE repo=? AND sha=? AND finding=?",
                       (evidence["classification"], json.dumps(evidence), repo, sha, finding))


def _clean_snapshot(source: Path, destination: Path):
    source = source.resolve(strict=True)
    paths = list(source.rglob("*"))
    if any(p.is_symlink() or (p.is_file() and p.stat().st_nlink != 1) for p in paths):
        raise ProposalRejected("Snapshot links rejected")
    allowed = [p for p in paths if p.is_file()]
    if not allowed or len(allowed) > 128 or sum(p.stat().st_size for p in allowed) > 1048576:
        raise ProposalRejected("Snapshot size cap exceeded")
    for path in allowed:
        relative = path.relative_to(source).as_posix()
        if relative != "app.py" and not re.fullmatch(r"tests/test_[a-zA-Z0-9_]+\.py", relative):
            raise ProposalRejected("Unsupported repository files/configuration")
        data = path.read_bytes()
        if len(data) > MAX_SOURCE_BYTES:
            raise ProposalRejected("Source byte cap exceeded")
        if relative == "app.py":
            validate_source(data.decode("utf-8"), test=False)
        else:
            tree = ast.parse(data.decode("utf-8"))
            functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)]
            if len(functions) != 1 or not functions[0].name.startswith("test_"):
                raise ProposalRejected("Unsupported existing test infrastructure")
            validate_source(data.decode("utf-8"), test=True, test_function=functions[0].name)
        destination_path = destination / relative
        destination_path.parent.mkdir(parents=True, exist_ok=True)
        destination_path.write_bytes(data)
    if not (destination / "app.py").is_file() or not (destination / "tests").is_dir():
        raise ProposalRejected("Target source/existing tests missing")


def _passed(result: dict) -> bool:
    report = result.get("controller_report")
    return (result["returncode"] == 0 and result["limit_reason"] is None and report is not None
            and report["exitstatus"] == 0 and report["collected"] > 0
            and report.get("seccomp_installed") is True
            and len(report["calls"]) == report["collected"]
            and all(call["outcome"] == "passed" and not call["xfail"] for call in report["calls"]))


def verify_proposal(snapshot: Path, finding: dict, raw: str, export: Path, *, review_diff: str, identity: dict | None = None, proposal_kind: str = "mock") -> dict:
    if proposal_kind not in ("mock", "live"):
        raise ValueError("Explicit mock/live proposal origin required")
    evidence = {"schema_version": 1, "kind": proposal_kind, "classification": "ERROR", "finding": finding,
                "provider_calls": 0, "usage": None, "cost_usd": 0, "patch_export": None,
                "source_root_unchanged": None}
    watched_before = None
    if identity:
        if set(identity) - {"repo", "reviewed_commit", "finding_index", "seeded_case", "corpus_version", "test_manifest_sha256"}:
            raise ValueError("Unexpected controller identity fields")
        evidence.update(identity)
    try:
        if len(review_diff.encode()) > 12000:
            raise ProposalRejected("Review diff cap exceeded")
        validated = validate_findings(json.dumps({"findings": [finding]}), review_diff, ["app.py"])
        if len(validated["findings"]) != 1:
            raise ProposalRejected("Finding lacks validated added-line citation")
        finding = validated["findings"][0]
        evidence.update(finding=finding, review_diff_sha256=source_hash(review_diff.encode()))
        proposal = validate_proposal(raw, finding)
        with tempfile.TemporaryDirectory(prefix="steward-act-") as temporary:
            workspace = Path(temporary) / "workspace"
            workspace.mkdir()
            _clean_snapshot(snapshot, workspace)
            watched_before = {p.relative_to(snapshot).as_posix(): source_hash(p.read_bytes()) for p in snapshot.rglob("*") if p.is_file()}
            before_hashes = {p.relative_to(workspace).as_posix(): source_hash(p.read_bytes()) for p in workspace.rglob("*") if p.is_file()}
            original = (workspace / "app.py").read_text(encoding="utf-8")
            lines = original.splitlines()
            if finding["line"] > len(lines) or lines[finding["line"]-1].strip() != finding["evidence"].strip():
                raise ProposalRejected("Citation does not match materialized source")
            test = proposal["test_source"].encode()
            test_path = workspace / "test_reproducer.py"
            test_path.write_bytes(test)
            evidence.update(source_hashes=before_hashes, test_source=proposal["test_source"], test_sha256=source_hash(test), proposal_sha256=source_hash(raw.encode()))
            evidence["existing_before"] = run_tests(workspace, ["tests"])
            if not _passed(evidence["existing_before"]):
                evidence["reason"] = "Existing test baseline did not pass"
            else:
                before = run_tests(workspace, ["test_reproducer.py"])
                evidence["reproducer_before"] = before
                expected = proposal["expected_failure"]
                report = before.get("controller_report")
                reproduced = (before["returncode"] == 1 and before["limit_reason"] is None and report is not None
                              and report["exitstatus"] == 1 and report["collected"] == 1 and len(report["calls"]) == 1
                              and report.get("seccomp_installed") is True
                              and report["calls"][0]["outcome"] == "failed" and report["calls"][0]["exception"] == expected
                              and not report["calls"][0]["xfail"])
                if not reproduced:
                    evidence["classification"] = "NOT_REPRODUCED"
                elif proposal["replacement_source"] is None:
                    evidence["classification"] = "REPRODUCED"
                else:
                    replacement = proposal["replacement_source"]
                    (workspace / "app.py").write_text(replacement, encoding="utf-8", newline="\n")
                    if source_hash(test_path.read_bytes()) != source_hash(test):
                        evidence["classification"] = "TAMPERED"
                    else:
                        # Test and public tests stay byte-identical; source is read-only inside worker.
                        for name, expected_hash in before_hashes.items():
                            if name != "app.py" and source_hash((workspace / name).read_bytes()) != expected_hash:
                                raise ProposalRejected("Existing test tampered")
                        after = run_tests(workspace, ["test_reproducer.py", "tests"])
                        evidence["after"] = after
                        if source_hash(test_path.read_bytes()) != source_hash(test):
                            raise ProposalRejected("Reproducer changed after execution")
                        evidence["classification"] = "PATCH_VERIFIED" if _passed(after) else "PATCH_FAILED"
                        evidence["patch_diff"] = "".join(difflib.unified_diff(original.splitlines(keepends=True), replacement.splitlines(keepends=True), fromfile="a/app.py", tofile="b/app.py"))
                        evidence["patch_sha256"] = source_hash(evidence["patch_diff"].encode())
                        if evidence["classification"] == "PATCH_VERIFIED":
                            export.mkdir(parents=True, exist_ok=True)
                            patch = export / (evidence["patch_sha256"] + ".patch")
                            if patch.exists() and patch.read_bytes() != evidence["patch_diff"].encode():
                                raise ProposalRejected("Export collision")
                            patch.write_bytes(evidence["patch_diff"].encode())
                            evidence["patch_export"] = patch.name
    except ProposalRejected as exc:
        evidence.update(classification="TAMPERED", reason=str(exc))
    except (RuntimeError, OSError, UnicodeError, ValueError) as exc:
        evidence.update(classification="ERROR", reason=type(exc).__name__)
    if watched_before is not None:
        watched_after = {p.relative_to(snapshot).as_posix(): source_hash(p.read_bytes()) for p in snapshot.rglob("*") if p.is_file()}
        evidence["source_root_unchanged"] = watched_before == watched_after
        if not evidence["source_root_unchanged"]:
            evidence.update(classification="TAMPERED", reason="Original snapshot changed", patch_export=None)
    export.mkdir(parents=True, exist_ok=True)
    evidence["lock_sha256"] = source_hash(Path("requirements-steward-eval-lock.txt").read_bytes())
    name = source_hash(canonical(evidence)) + ".json"
    (export / name).write_bytes(canonical(evidence))
    return evidence
