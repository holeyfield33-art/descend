"""B0/B1 on owned corpus: existing tests and ruff, with Linux isolation only."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
import time
from pathlib import Path

from descend.sandbox.hard_isolation import isolation_available, run_in_hard_isolation
from descend.steward.corpus import canonical, verify_manifest
from descend.steward.findings import added_lines
from scripts.check_steward_corpus import RUNNER


def run_baselines(corpus: Path, output: Path):
    if sys.platform != "linux" or not isolation_available()["available"]:
        raise RuntimeError("Baselines require isolated Linux; no fallback")
    manifest = verify_manifest(corpus)
    records = []
    for case in manifest["cases"]:
        start = time.monotonic()
        stages = {}
        for stage in ("base", "review"):
            with tempfile.TemporaryDirectory(prefix="steward-baseline-") as temporary:
                root = Path(temporary)
                workspace = root / "agent" / "workspace"
                shutil.copytree(corpus / "cases" / case["id"] / stage, workspace)
                script = """import json, os, subprocess
os.chdir('/workspace')
env = {'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8', 'HOME': '/workspace', 'PYTEST_DISABLE_PLUGIN_AUTOLOAD': '1', 'PYTHONDONTWRITEBYTECODE': '1'}
def run(argv):
    p = subprocess.run(argv, env=env, capture_output=True, text=True, timeout=10)
    return {'argv': argv, 'returncode': p.returncode, 'stdout': p.stdout[:16000], 'stderr': p.stderr[:4000]}
versions = run([RUNNER, '-c', 'import pytest; import importlib.metadata as m; print(pytest.__version__, m.version("ruff"))'])
assert versions['returncode'] == 0 and versions['stdout'].strip() == '9.1.1 0.16.10', versions
tests = run([RUNNER, '-m', 'pytest', '-q', '--tb=short', '-p', 'no:cacheprovider', 'tests'])
lint = run([RUFF, 'check', '--isolated', '--no-cache', '--output-format', 'json', 'app.py'])
print(json.dumps({'tests': tests, 'lint': lint, 'versions': versions}))
""".replace("RUNNER", repr(RUNNER)).replace("RUFF", repr(str(Path(RUNNER).with_name("ruff"))))
                raw = run_in_hard_isolation(script, workspace=workspace, controller_root=root / "controller", timeout_sec=30, memory_mb=512)
                stages[stage] = json.loads(raw["stdout"]) if raw["ok"] else {"error": raw}
        findings = []
        error = None
        if any("error" in s for s in stages.values()):
            error = "worker_error"
        elif any(s["lint"]["returncode"] not in (0, 1) or s["tests"]["returncode"] not in (0, 1) for s in stages.values()):
            error = "baseline_tool_error"
        else:
            diff = (corpus / "cases" / case["id"] / "review.diff").read_text(encoding="utf-8")
            additions = added_lines(diff)
            base_lint = json.loads(stages["base"]["lint"]["stdout"])
            review_lint = json.loads(stages["review"]["lint"]["stdout"])
            prior = {(Path(row["filename"]).name, row["code"], row["message"]) for row in base_lint}
            for row in review_lint:
                path, line = Path(row["filename"]).name, row["location"]["row"]
                if (path, row["code"], row["message"]) not in prior and (path, line) in additions:
                    findings.append({"path": path, "line": line, "evidence": additions[path, line], "severity": "low",
                                     "reason": f"ruff {row['code']}: {row['message']}", "verification": "New diagnostic relative to base"})
            if stages["review"]["tests"]["returncode"] == 1 and stages["base"]["tests"]["returncode"] == 0:
                for match in re.finditer(r"(?:/workspace/)?app\.py:(\d+):", stages["review"]["tests"]["stdout"]):
                    line = int(match.group(1))
                    if ("app.py", line) in additions:
                        findings.append({"path": "app.py", "line": line, "evidence": additions["app.py", line], "severity": "medium",
                                         "reason": "New existing-test failure on an added source line", "verification": "Controller-run baseline comparison"})
        records.append({"case": case["id"], "content": json.dumps({"findings": findings}), "error": error,
                        "latency_seconds": time.monotonic()-start, "stages": stages,
                        "tokens": None, "accounted_upper_bound_usd": 0})
    output.mkdir(parents=True, exist_ok=True)
    metadata = {"corpus_version": manifest["version"], "provider_calls": 0,
                "test_manifest_sha256": hashlib.sha256((corpus / "test-manifest.json").read_bytes()).hexdigest(),
                "eval_lock_sha256": hashlib.sha256(Path("requirements-steward-eval-lock.txt").read_bytes()).hexdigest()}
    (output / "B1.json").write_bytes(canonical({**metadata, "arm": "B1", "results": records}))
    (output / "B0.json").write_bytes(canonical({**metadata, "arm": "B0", "results": [{"case": c["id"], "content": '{"findings": []}', "accounted_upper_bound_usd": 0} for c in manifest["cases"]]}))
    return {"cases": len(records), "errors": sum(bool(r["error"]) for r in records), "provider_calls": 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus", type=Path, default=Path("eval/v1"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_baselines(args.corpus, args.output)
    print(json.dumps(result))
    raise SystemExit(bool(result["errors"]))


if __name__ == "__main__":
    main()
