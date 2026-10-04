"""Hard OS isolation for agent code using Linux namespaces + chroot.

When Docker is unavailable, this module uses ``unshare`` to create:

* a new **mount** namespace with a minimal chroot (no host /home, /root, controller)
* a new **network** namespace with no external interfaces (no egress)
* a new **PID** namespace so host controller processes are not visible
* execution as non-root UID 65534 (nobody) when possible

This is an OS-enforced boundary, not path sanitization.

Claim scope (honest):
  Arbitrary code running under the permissions granted to the Descend agent
  namespace could not directly read or mutate controller-owned assets in the
  tested attacks. Namespaces/chroot are not mathematically perfect isolation.
"""

from __future__ import annotations

import os
import shutil
import shlex
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, Optional


ISOLATION_RUNTIME = "linux-namespaces-unshare-chroot"
NOBODY_UID = 65534
NOBODY_GID = 65534


def isolation_available() -> Dict[str, Any]:
    unshare = shutil.which("unshare")
    info = {
        "runtime": ISOLATION_RUNTIME,
        "unshare_path": unshare,
        "available": unshare is not None and sys.platform == "linux",
        "uid": os.getuid() if hasattr(os, "getuid") else None,
        "euid": os.geteuid() if hasattr(os, "geteuid") else None,
        "is_root": hasattr(os, "geteuid") and os.geteuid() == 0,
    }
    if not info["available"]:
        info["reason"] = "unshare not found or non-POSIX host"
    else:
        try:
            probe = subprocess.run([unshare, "--mount", "--net", "--pid", "--fork", "true"],
                                   capture_output=True, timeout=3,
                                   env={"PATH": "/usr/bin:/bin", "LANG": "C"})
            if probe.returncode != 0 or not info["is_root"]:
                info["available"] = False
                info["reason"] = "namespace/chroot privileges unavailable"
        except (OSError, subprocess.TimeoutExpired):
            info["available"] = False
            info["reason"] = "namespace privilege probe failed"
    return info


def build_agent_root(workspace: Path, *, controller_root: Path) -> Path:
    agent_root = workspace.parent / "agent_root"
    if agent_root.exists():
        shutil.rmtree(agent_root)
    agent_root.mkdir(parents=True)
    (agent_root / "workspace").mkdir()
    (agent_root / "tmp").mkdir()
    (agent_root / "README_ISOLATION.txt").write_text(
        "Agent jail filesystem. Controller directories are not mounted.\n"
        f"Host controller root (NOT mounted): {controller_root}\n",
        encoding="utf-8",
    )
    return agent_root


def _prepare_workspace_permissions(workspace: Path, script_path: Path) -> None:
    try:
        os.chmod(workspace, 0o777)
        os.chmod(script_path, 0o755)
        for root, dirs, files in os.walk(workspace):
            for d in dirs:
                os.chmod(Path(root) / d, 0o777)
            for f in files:
                os.chmod(Path(root) / f, 0o755)
        if os.geteuid() == 0:
            for root, dirs, files in os.walk(workspace):
                os.chown(root, NOBODY_UID, NOBODY_GID)
                for d in dirs:
                    os.chown(Path(root) / d, NOBODY_UID, NOBODY_GID)
                for f in files:
                    os.chown(Path(root) / f, NOBODY_UID, NOBODY_GID)
    except OSError:
        pass


def run_in_hard_isolation(
    script_source: str,
    *,
    workspace: Path,
    controller_root: Path,
    timeout_sec: float = 30.0,
    memory_mb: int = 256,
    tool_handler=None,
) -> Dict[str, Any]:
    """
    Execute script_source inside hard-isolated Linux namespaces + chroot.

    - network: unshare --net (no egress)
    - filesystem: chroot minimal root; only workspace writable
    - pid: new namespace
    - uid: nobody (65534) when root
    """
    avail = isolation_available()
    if not avail["available"]:
        return {
            "ok": False,
            "error": "hard isolation unavailable",
            "isolation": avail,
            "returncode": -1,
            "stdout": "",
            "stderr": avail.get("reason", "unavailable"),
        }

    workspace = workspace.resolve()
    controller_root = controller_root.resolve()
    if workspace == controller_root or workspace in controller_root.parents or controller_root in workspace.parents:
        raise ValueError("controller and workspace must be disjoint")
    for runtime_dir in ("/usr", "/lib", "/lib64", "/bin"):
        runtime_path = Path(runtime_dir).resolve()
        if controller_root == runtime_path or runtime_path in controller_root.parents:
            raise ValueError("controller assets must be outside runtime mounts")
    workspace.mkdir(parents=True, exist_ok=True)
    for path in workspace.rglob("*"):
        if path.is_symlink() or (path.is_file() and path.stat().st_nlink != 1):
            raise ValueError("workspace links are not allowed")

    agent_root = build_agent_root(workspace, controller_root=controller_root)
    script_path = workspace / "_isolated_agent.py"
    script_path.write_text(script_source, encoding="utf-8")
    _prepare_workspace_permissions(workspace, script_path)

    wrapper = agent_root / "enter.sh"
    py = sys.executable
    wrapper_body = textwrap.dedent(
        """\
        #!/bin/bash
        set -e
        mount --make-rprivate /
        ulimit -v __MEMORY_KB__

        ROOT=__CHROOT__
        mkdir -p "$ROOT"/{workspace,tmp,proc,dev,usr,lib,lib64,bin,etc}

        for d in /usr /lib /lib64 /bin; do
          if [ -d "$d" ]; then
            mkdir -p "$ROOT$d"
            mount --bind "$d" "$ROOT$d"
            mount -o remount,ro,bind "$ROOT$d"
          fi
        done
        touch "$ROOT/etc/passwd" "$ROOT/etc/group" 2>/dev/null || true

        mount --bind __WORKSPACE__ "$ROOT/workspace"
        mount -t tmpfs -o size=32m,mode=1777 tmpfs "$ROOT/tmp"
        mount -t proc proc "$ROOT/proc" 2>/dev/null || true

        export HOME=/workspace
        export TMPDIR=/tmp
        export PYTHONPATH=
        unset NEBIUS_API_KEY HF_TOKEN HUGGINGFACE_TOKEN OPENAI_API_KEY
        unset DESCEND_CONTROLLER_ROOT DESCEND_REGISTRY_PATH DESCEND_HIDDEN_SEED
        unset API_KEY API_SECRET

        INNER_PY=__PYTHON__
        if [ ! -x "$ROOT$INNER_PY" ]; then
          INNER_PY=/usr/bin/python3
        fi

        cd "$ROOT"
        if [ "$(id -u)" = "0" ]; then
          exec chroot "$ROOT" setpriv --reuid=__UID__ --regid=__GID__ --clear-groups --no-new-privs --bounding-set=-all -- \\
            "$INNER_PY" /workspace/_isolated_agent.py
        else
          exec chroot "$ROOT" "$INNER_PY" /workspace/_isolated_agent.py
        fi
        """
    )
    wrapper_body = (
        wrapper_body.replace("__CHROOT__", shlex.quote(str(agent_root / "chroot")))
        .replace("__WORKSPACE__", shlex.quote(str(workspace)))
        .replace("__PYTHON__", shlex.quote(py))
        .replace("__UID__", str(NOBODY_UID))
        .replace("__GID__", str(NOBODY_GID))
        .replace("__MEMORY_KB__", str(int(memory_mb) * 1024))
    )
    wrapper.write_text(wrapper_body, encoding="utf-8")
    wrapper.chmod(0o755)

    unshare = shutil.which("unshare")
    assert unshare
    cmd = [
        unshare,
        "--mount",
        "--net",
        "--pid",
        "--fork",
        "--kill-child=KILL",
        "--mount-proc",
        str(wrapper),
    ]
    env = {
        "PATH": "/usr/bin:/bin",
        "LANG": "C",
        "HOME": "/workspace",
        "TMPDIR": "/tmp",
    }
    try:
        if tool_handler is not None:
            return _run_tool_process(cmd, env, timeout_sec, tool_handler, avail)
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_sec,
            env=env,
        )
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "isolation": {
                **avail,
                "network": "none (unshare --net)",
                "mount": "chroot minimal root + workspace bind",
                "pid": "new namespace",
                "uid_target": NOBODY_UID,
                "controller_root_not_mounted": True,
                "workspace": str(workspace),
            },
            "timed_out": False,
        }
    except subprocess.TimeoutExpired as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": e.stdout or "",
            "stderr": e.stderr or "timeout",
            "isolation": avail,
            "timed_out": True,
        }
    except OSError as e:
        return {
            "ok": False,
            "returncode": -1,
            "stdout": "",
            "stderr": str(e),
            "isolation": avail,
            "timed_out": False,
        }


def _run_tool_process(cmd, env, timeout, handler, isolation):
    """Bounded newline JSON transport on inherited pipes; no listening socket."""
    import json
    import queue
    import signal
    import threading
    import time
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.DEVNULL, env=env, start_new_session=True)
    messages = queue.Queue(maxsize=16)
    stopping = threading.Event()
    def reader():
        try:
            while True:
                line = proc.stdout.readline(65537)
                while not stopping.is_set():
                    try:
                        messages.put(line, timeout=0.1)
                        break
                    except queue.Full:
                        continue
                if not line or len(line) > 65536:
                    return
        except (OSError, ValueError):
            pass
    threading.Thread(target=reader, daemon=True).start()
    deadline = time.monotonic() + timeout
    result = None
    error = None
    try:
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("agent deadline exceeded")
            line = messages.get(timeout=remaining)
            if not line:
                break
            if len(line) > 65536:
                raise ValueError("oversized request")
            request = json.loads(line)
            if not isinstance(request, dict):
                raise ValueError("invalid request")
            if request.get("type") == "result":
                result = request.get("result")
                break
            try:
                response = {"ok": True, "result": handler(request)}
            except Exception as exc:
                from descend.controller.budgets import BudgetExhausted
                if isinstance(exc, BudgetExhausted):
                    raise
                response = {"ok": False, "error": "tool request rejected"}
            proc.stdin.write((json.dumps(response) + "\n").encode())
            proc.stdin.flush()
        proc.wait(timeout=max(0.01, deadline - time.monotonic()))
    except Exception as exc:
        error = type(exc).__name__
    finally:
        stopping.set()
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        proc.wait()
        proc.stdin.close()
        proc.stdout.close()
    return {"ok": error is None and proc.returncode == 0 and result is not None,
            "result": result, "returncode": proc.returncode, "error": error,
            "isolation": isolation, "stdout": "", "stderr": "",
            "timed_out": error in ("TimeoutError", "Empty")}


def probe_script() -> str:
    return textwrap.dedent(
        """\
        import json, os, socket
        result = {
            "uid": os.getuid(),
            "euid": os.geteuid(),
            "cwd": os.getcwd(),
            "env_keys": sorted(os.environ.keys()),
            "secret_env": [],
            "has_controller_env": False,
            "mounts": [],
            "proc_self_status_uid": None,
            "can_see_pid1_environ": False,
            "network_tcp": None,
            "network_dns": None,
            "found_controller_paths": [],
            "workspace_writable": False,
            "list_root": [],
        }
        bad = ("NEBIUS", "HF_TOKEN", "HUGGINGFACE", "API_KEY", "API_SECRET",
               "DESCEND_CONTROLLER", "DESCEND_HIDDEN", "DESCEND_REGISTRY", "PASSWORD", "SECRET")
        for k in os.environ:
            ku = k.upper()
            if any(b in ku for b in bad):
                result["secret_env"].append(k)
            if "CONTROLLER" in ku or "HIDDEN" in ku:
                result["has_controller_env"] = True
        try:
            with open("/proc/self/mounts") as f:
                result["mounts"] = [line.strip() for line in f.readlines()[:40]]
        except Exception as e:
            result["mounts_error"] = str(e)
        try:
            with open("/proc/self/status") as f:
                for line in f:
                    if line.startswith("Uid:"):
                        result["proc_self_status_uid"] = line.strip()
        except Exception as e:
            result["status_error"] = str(e)
        try:
            with open("/proc/1/environ", "rb") as f:
                data = f.read()
                result["can_see_pid1_environ"] = bool(data)
                result["pid1_environ_len"] = len(data)
        except Exception as e:
            result["pid1_environ_error"] = type(e).__name__
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)
            s.connect(("1.1.1.1", 443))
            result["network_tcp"] = "CONNECTED"
            s.close()
        except Exception as e:
            result["network_tcp"] = "BLOCKED:" + type(e).__name__
        try:
            socket.getaddrinfo("example.com", 80)
            result["network_dns"] = "RESOLVED"
        except Exception as e:
            result["network_dns"] = "BLOCKED:" + type(e).__name__
        for p in ["/controller", "/controller_state", "/registry", "/hidden",
                  "/home", "/root", "/var/run/docker.sock", "/run/docker.sock"]:
            if os.path.exists(p):
                result["found_controller_paths"].append(p)
        try:
            result["list_root"] = sorted(os.listdir("/"))[:30]
        except Exception as e:
            result["list_root_error"] = str(e)
        try:
            open("/workspace/probe_write.txt", "w").write("ok")
            result["workspace_writable"] = True
        except Exception as e:
            result["workspace_write_error"] = str(e)
        result["cwd"] = os.getcwd()
        print(json.dumps(result))
        """
    )


def mock_tool_proxy_echo(request: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tool": request.get("tool", "echo"),
        "status": "ok",
        "mediated_by": "controller",
        "echo": request.get("payload"),
        "note": "Produced by controller outside agent namespace; agent has no direct network.",
    }
