"""Offline canned act proposal: detached Git/corpus source, export only."""
from __future__ import annotations

import argparse
import json
import re
import tempfile
from pathlib import Path

from descend.steward.act import ActStore, verify_proposal
from descend.steward.corpus import verify_manifest
from descend.steward.findings import added_lines
from descend.steward.watch import ReviewStore, _git


def materialize_git(repo: Path, sha: str, destination: Path) -> str:
    if not re.fullmatch(r"[0-9a-f]{40}", sha):
        raise ValueError("Full reviewed commit SHA required")
    actual = _git(repo, "rev-parse", "--verify", sha + "^{commit}").decode().strip()
    if actual != sha:
        raise ValueError("Commit identity mismatch")
    rows = _git(repo, "ls-tree", "-r", "-z", sha).split(b"\0")
    if len(rows) > 129:
        raise ValueError("Repository file cap exceeded")
    total = 0
    for row in rows:
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        mode, kind, oid = metadata.decode("ascii").split()
        name = raw_path.decode("utf-8", errors="strict")
        if mode not in ("100644", "100755") or kind != "blob":
            raise ValueError("Repository links/submodules rejected")
        # Initial act scope: module + tests; README/attribution may stay outside.
        if name in ("README.md", "LICENSE", ".gitignore", ".gitattributes"):
            continue
        if name != "app.py" and not re.fullmatch(r"tests/test_[a-zA-Z0-9_]+\.py", name):
            raise ValueError("Unsupported repository files or configuration")
        size = int(_git(repo, "cat-file", "-s", oid).strip())
        total += size
        if size > 12000 or total > 1048576:
            raise ValueError("Source size cap exceeded")
        data = _git(repo, "cat-file", "blob", oid)
        if len(data) != size:
            raise ValueError("Git blob size changed")
        target = destination / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    lineage = _git(repo, "rev-list", "--parents", "-n", "1", sha).decode().split()
    if len(lineage) > 1:
        return _git(repo, "diff", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", lineage[1], sha, "--", "app.py").decode("utf-8")
    return _git(repo, "show", "--format=", "--no-ext-diff", "--no-textconv", "--ignore-submodules=all", sha, "--", "app.py").decode("utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--case", help="Owned frozen corpus case ID")
    source.add_argument("--repo", type=Path, help="Explicit reviewed owned checkout")
    parser.add_argument("--sha")
    parser.add_argument("--finding", type=int, default=0)
    parser.add_argument("--reviews-db", type=Path, default=Path("controller_state/steward-reviews-v2.sqlite"))
    parser.add_argument("--corpus", type=Path, default=Path("eval/v1"))
    parser.add_argument("--proposal", type=Path, required=True, help="Canned JSON; no provider call")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--state", type=Path, default=Path("controller_state/steward-act-mock.sqlite"))
    parser.add_argument("--commit-cap", type=int, default=1)
    args = parser.parse_args()
    store = ActStore(args.state)
    if args.proposal.stat().st_size > 24000:
        parser.error("Proposal byte cap exceeded")
    raw = args.proposal.read_text(encoding="utf-8")
    with tempfile.TemporaryDirectory(prefix="steward-git-snapshot-") as temporary:
        if args.case:
            manifest = verify_manifest(args.corpus)
            if args.case not in {case["id"] for case in manifest["cases"]}:
                parser.error("Unknown corpus case")
            directory = args.corpus / "cases" / args.case
            snapshot = directory / "review"
            diff = (directory / "review.diff").read_text(encoding="utf-8")
            additions = added_lines(diff)
            if not additions:
                parser.error("Case has no added citation")
            (path, line), evidence = next(iter(additions.items()))
            finding = {"path": path, "line": line, "evidence": evidence, "severity": "low",
                       "reason": "MOCK seeded finding, not a model review", "verification": "Controller-run reproducer"}
            repo_id, sha = "seeded:" + args.case, manifest["version"]
        else:
            if not args.sha:
                parser.error("--repo requires --sha")
            repo = args.repo.resolve(strict=True)
            row = ReviewStore(args.reviews_db).get(str(repo), args.sha)
            findings = (row or {}).get("review", {}).get("findings", [])
            if not 0 <= args.finding < len(findings):
                parser.error("No stored validated finding at this index")
            finding = findings[args.finding]
            snapshot = Path(temporary) / "source"
            snapshot.mkdir()
            diff = materialize_git(repo, args.sha, snapshot)
            repo_id, sha = str(repo), args.sha
        if not store.claim(repo_id, sha, args.finding, commit_cap=args.commit_cap):
            parser.exit(1, "Action already claimed or commit cap exhausted; no automatic retry\n")
        result = verify_proposal(snapshot, finding, raw, args.output, review_diff=diff,
                                 identity={"repo": repo_id, "reviewed_commit": sha, "finding_index": args.finding})
        store.finish(repo_id, sha, args.finding, result)
        print(json.dumps(result, indent=2))
        raise SystemExit(0 if result["classification"] in ("PATCH_VERIFIED", "REPRODUCED") else 1)


if __name__ == "__main__":
    main()
