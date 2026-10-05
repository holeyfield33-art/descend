"""Offline runtime manifest. Reads no credentials and makes no provider request."""
from __future__ import annotations

import hashlib
import importlib.metadata
import platform
import shutil
import sys
from pathlib import Path

from descend.sandbox.hard_isolation import isolation_available


def diagnose(root: Path) -> dict:
    root = root.resolve(strict=True)
    lock = root / "requirements-lock.txt"
    pin_file = ".python-version.windows" if sys.platform == "win32" else ".python-version"
    pin = (root / pin_file).read_text(encoding="utf-8").strip()
    helpers = {name: shutil.which(name) for name in ("git", "unshare", "chroot", "setpriv", "mount")}
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
    return {"schema_version": 1, "python": platform.python_version(), "python_pin": pin,
            "python_pin_file": pin_file,
            "platform": sys.platform, "helpers": helpers,
            "lock_sha256": hashlib.sha256(lock.read_bytes()).hexdigest(),
            "dependency_mismatches": mismatches, "isolation": isolation,
            "protocol_ready": protocol_ready,
            "act_ready": False,
            "act_reason": "Act worker not implemented; prerequisites alone are not readiness",
            "provider_calls": 0}
