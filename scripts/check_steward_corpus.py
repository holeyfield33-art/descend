"""Validate owned frozen fixtures only in the Linux namespace worker."""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
from pathlib import Path

from descend.sandbox.hard_isolation import isolation_available, run_in_hard_isolation
from descend.steward.corpus import canonical, verify_manifest

RUNNER = "/usr/local/lib/steward-test-runtime/bin/python"


def check_corpus(root: Path, output: Path) -> dict:
    if sys.platform != "linux" or not isolation_available()["available"]:
        raise RuntimeError("Corpus execution requires Linux namespace isolation; no fallback")
    if not Path(RUNNER).is_file():
        raise RuntimeError("Pinned pytest runtime is missing")
    manifest = verify_manifest(root)
    records = []
    for case in manifest["cases"]:
        stages = ("review", "fix") if case["label"] == "bug" else ("review",)
        for stage in stages:
            with tempfile.TemporaryDirectory(prefix="steward-corpus-") as temporary:
                base = Path(temporary)
                workspace = base / "agent" / "workspace"
                source = root / "cases" / case["id"]
                shutil.copytree(source / stage, workspace)
                if case["label"] == "bug":
                    shutil.copyfile(source / "test_reproducer.py", workspace / "test_reproducer.py")
                # Trusted fixed command, no source-selected argv, no provider or env secrets.
                script = """import os, subprocess, json
os.chdir('/workspace')
argv = [RUNNER, '-m', 'pytest', '-q', '--tb=short', '-p', 'no:cacheprovider', 'tests']
if os.path.exists('/workspace/test_reproducer.py'):
    argv.append('test_reproducer.py')
env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'HOME': '/workspace',
       'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
version = subprocess.run([RUNNER, '-c', 'import pytest; print(pytest.__version__)'], capture_output=True, text=True, env=env, check=True)
assert version.stdout.strip() == '9.1.1', 'pytest runtime version mismatch'
result = subprocess.run(argv, capture_output=True, text=True, env=env, timeout=10)
print(json.dumps({'returncode': result.returncode, 'stdout': result.stdout[:16000],
                  'stderr': result.stderr[:4000], 'pytest': version.stdout.strip(), 'argv': argv}))
""".replace("RUNNER", repr(RUNNER))
                result = run_in_hard_isolation(script, workspace=workspace, controller_root=base / "controller", timeout_sec=20, memory_mb=512)
                expected = 1 if case["label"] == "bug" and stage == "review" else 0
                observed = None
                if result["ok"]:
                    try:
                        observed = json.loads(result["stdout"])
                    except (ValueError, TypeError):
                        pass
                passed = observed is not None and observed["returncode"] == expected
                if expected == 1 and passed:
                    passed = "1 failed, 1 passed" in observed["stdout"] and "ERROR collecting" not in observed["stdout"]
                records.append({"case": case["id"], "split": case["split"], "label": case["label"],
                                "stage": stage, "expected_exit": expected, "label_validated": passed,
                                "result": observed, "worker_error": None if result["ok"] else result,
                                "snapshot_hashes": {k: v for k, v in case["files"].items() if k.startswith(stage + "/") or k == "test_reproducer.py"}})
                if not passed:
                    # Preserve the first unexplained mismatch and stop for investigation.
                    break
        if not records[-1]["label_validated"]:
            break
    report = {"schema_version": 1, "corpus_version": manifest["version"],
              "manifest_sha256": hashlib.sha256((root / "manifest.json").read_bytes()).hexdigest(),
              "test_manifest_sha256": hashlib.sha256((root / "test-manifest.json").read_bytes()).hexdigest(),
              "lock_sha256": hashlib.sha256(Path("requirements-lock.txt").read_bytes()).hexdigest(),
              "controller_python": sys.version.split()[0], "test_runner": RUNNER,
              "records": records, "validated": sum(r["label_validated"] for r in records),
              "expected_runs": 68, "complete": len(records) == 68 and all(r["label_validated"] for r in records),
              "provider_calls": 0}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(canonical(report))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("eval/v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = check_corpus(args.corpus, args.output)
    print(json.dumps({key: report[key] for key in ("complete", "validated", "expected_runs", "provider_calls")}))
    raise SystemExit(0 if report["complete"] else 1)


if __name__ == "__main__":
    main()
