"""Offline runtime manifest. Reads no credentials and makes no provider request."""
from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import shutil
import sys
import tempfile
from pathlib import Path

from descend.sandbox.hard_isolation import isolation_available
from descend.steward.act_worker import LIMITS, PYTHON, run_tests


def diagnose(root: Path, *, probe_act: bool = False) -> dict:
    root = root.resolve(strict=True)
    lock = root / "requirements-lock.txt"
    pin_file = ".python-version.windows" if sys.platform == "win32" else ".python-version"
    pin = (root / pin_file).read_text(encoding="utf-8").strip()
    helpers = {name: shutil.which(name) for name in ("git", "unshare", "chroot", "setpriv", "mount", "mkdir", "touch")}
    helpers["test_runner_python"] = str(Path(sys.executable).absolute())
    helpers["test_runner_binary"] = str(Path(sys.executable).resolve())
    mismatches = []
    for row in lock.read_text(encoding="utf-8").splitlines():
        if not row or row.startswith("#"):
            continue
        name, expected = row.split("==", 1)
        try:
            actual = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            actual = None
        if actual != expected:
            mismatches.append({"package": name, "expected": expected, "actual": actual})
    isolation = isolation_available()
    protocol_ready = platform.python_version() == pin and not mismatches and helpers["git"] is not None
    act_ready = protocol_ready and sys.platform == "linux" and isolation["available"] and platform.machine() == "x86_64" and Path(PYTHON).is_file() and all(helpers[n] for n in ("unshare", "chroot", "setpriv", "mount", "mkdir", "touch"))
    probe = None
    if act_ready and probe_act:
        try:
            with tempfile.TemporaryDirectory(prefix="steward-doctor-") as temporary:
                workspace = Path(temporary)
                workspace.chmod(0o755)
                (workspace / "tests").mkdir()
                (workspace / "tests/test_runtime.py").write_text("def test_runtime():\n    assert True\n", encoding="utf-8")
                probe = run_tests(workspace, ["tests"])
                act_ready = (probe["returncode"] == 0 and (probe.get("controller_report") or {}).get("seccomp_installed") is True)
        except (RuntimeError, OSError, ValueError) as exc:
            probe = {"error_type": type(exc).__name__}
            act_ready = False
    return {"schema_version": 1, "python": platform.python_version(), "python_pin": pin,
            "python_pin_file": pin_file,
            "platform": sys.platform, "helpers": helpers,
            "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
            "dependency_mismatches": mismatches, "isolation": isolation,
            "protocol_ready": protocol_ready,
            "act_ready": bool(act_ready), "act_runtime_python": PYTHON,
            "act_scope": "Restricted app.py solve(values) and assertion tests; export only",
            "act_limits": LIMITS,
            "act_runtime_probe": probe,
            "act_reason": "Runtime prerequisites ready; consult measured tests for assurance" if act_ready else "Linux privilege or pinned runtime prerequisites unavailable",
            "provider_calls": 0}
