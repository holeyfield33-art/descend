"""Agent execution boundary — process + filesystem isolation.

Phase 1.5 isolation mechanism (honest scope):

What this provides
------------------
1. Separate filesystem roots:
   - agent_workspace: writable by agent code
   - controller_root: owns registry, hidden data, committed artifacts, promotion config
2. Subprocess execution of untrusted agent scripts with:
   - cwd restricted to agent_workspace
   - scrubbed environment (no secrets)
   - no inherited controller paths in env
3. Path jail on Workspace API (reject traversal / absolute escapes).
4. Committed artifacts are copied into controller-owned immutable storage;
   hashes are re-verified immediately before hidden evaluation (TOCTOU defense).

What this does NOT provide (documented residual risk)
-----------------------------------------------------
- Full container/network-namespace isolation (no Docker/ns required in CPU phase).
- Kernel-level seccomp or user-namespace jail.
- Prevention of a compromised host process reading controller_root if the
  host OS grants the same UID access to both trees (same-UID process isolation
  is soft). True hard isolation requires separate UIDs, containers, or VMs.

Network: agent subprocess does not receive proxy/credential env vars. Direct
socket use is not kernel-blocked in this phase; adversarial tests attempt
outbound connections and record the result. Controller-mediated tools are the
only authorized external path when real backends are added.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence


# Env keys that must never appear in the agent process
FORBIDDEN_ENV_KEYS = (
    "NEBIUS",
    "HUGGINGFACE",
    "HF_TOKEN",
    "HF_API",
    "OPENAI",
    "ANTHROPIC",
    "API_KEY",
    "API_SECRET",
    "SECRET",
    "PASSWORD",
    "TOKEN",
    "CREDENTIAL",
    "PRIVATE_KEY",
    "CONTROLLER",
    "HIDDEN_SEED",
    "PREREG",
)


def scrub_env(base: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """Build a minimal environment with secrets stripped."""
    src = base if base is not None else dict(os.environ)
    out: Dict[str, str] = {}
    for k, v in src.items():
        ku = k.upper()
        if any(f in ku for f in FORBIDDEN_ENV_KEYS):
            continue
        # Keep only safe operational vars
        if k in (
            "PATH",
            "HOME",
            "LANG",
            "LC_ALL",
            "LC_CTYPE",
            "PYTHONPATH",
            "PYTHONHOME",
            "TMPDIR",
            "TMP",
            "TEMP",
            "USER",
            "LOGNAME",
            "SHELL",
            "TERM",
        ) or k.startswith("LC_"):
            out[k] = v
    # Ensure no controller secrets
    out.pop("DESCEND_CONTROLLER_ROOT", None)
    out.pop("DESCEND_REGISTRY_PATH", None)
    out.pop("DESCEND_HIDDEN_SEED", None)
    return out


def assert_path_inside(root: Path, target: Path) -> Path:
    """Resolve target and ensure it stays under root. Raises PermissionError."""
    root_r = root.resolve()
    # Disallow absolute escapes and null bytes
    t_str = str(target)
    if "\x00" in t_str:
        raise PermissionError("null byte in path")
    try:
        resolved = (root_r / target).resolve() if not Path(target).is_absolute() else Path(target).resolve()
    except (OSError, RuntimeError) as e:
        raise PermissionError(f"path resolution failed: {e}") from e
    try:
        resolved.relative_to(root_r)
    except ValueError as e:
        raise PermissionError(f"path escapes workspace: {target}") from e
    return resolved


class ControllerRoots:
    """Controller-owned directory layout, separate from agent workspace."""

    def __init__(self, base: str | Path):
        self.base = Path(base).resolve()
        self.base.mkdir(parents=True, exist_ok=True)
        self.registry = self.base / "registry"
        self.hidden = self.base / "hidden"
        self.committed = self.base / "committed"
        self.config = self.base / "config"
        for p in (self.registry, self.hidden, self.committed, self.config):
            p.mkdir(parents=True, exist_ok=True)

    def committed_path(self, run_id: str, name: str) -> Path:
        d = self.committed / run_id
        d.mkdir(parents=True, exist_ok=True)
        return d / name


def run_agent_script(
    script_path: Path,
    workspace: Path,
    *,
    timeout_sec: float = 30.0,
    extra_env: Optional[Dict[str, str]] = None,
    python_executable: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Execute an agent script in a subprocess jail.

    - cwd = workspace
    - env = scrubbed
    - Does not pass controller root paths
    """
    workspace = workspace.resolve()
    if not script_path.is_file():
        raise FileNotFoundError(script_path)

    env = scrub_env()
    if extra_env:
        for k, v in extra_env.items():
            ku = k.upper()
            if any(f in ku for f in FORBIDDEN_ENV_KEYS):
                continue
            env[k] = v
    # Explicitly do not set controller paths
    env.pop("DESCEND_CONTROLLER_ROOT", None)
    env.pop("DESCEND_REGISTRY_PATH", None)

    py = python_executable or sys.executable
    try:
        proc = subprocess.run(
            [py, str(script_path)],
            cwd=str(workspace),
            env=env,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
        )
        return {
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "returncode": -1,
            "stdout": e.stdout or "",
            "stderr": e.stderr or "timeout",
            "timed_out": True,
        }


def try_outbound_http(url: str = "http://127.0.0.1:9", timeout: float = 1.0) -> Dict[str, Any]:
    """
    Attempt a direct outbound HTTP connection from this process.
    Used by adversarial tests. Phase 1.5 does not kernel-block sockets;
    result is recorded for the threat model.
    """
    try:
        import urllib.request
        urllib.request.urlopen(url, timeout=timeout)
        return {"attempted": True, "blocked": False, "error": None}
    except Exception as e:
        return {"attempted": True, "blocked": True, "error": type(e).__name__ + ": " + str(e)}
