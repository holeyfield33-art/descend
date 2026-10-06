"""Constrained Linux pytest worker; no writable source mount or child processes."""
from __future__ import annotations

import os
import json
import selectors
import shlex
import shutil
import signal
import subprocess
import tempfile
import time
from pathlib import Path

from descend.sandbox.hard_isolation import isolation_available

PYTHON = "/usr/local/lib/steward-test-runtime/bin/python"
LIMITS = {"wall_seconds": 15, "cpu_seconds": 5, "memory_mb": 256,
          "output_bytes": 32768, "tmp_bytes": 8388608, "tmp_inodes": 256,
          "processes": 1, "open_files": 64, "source_files": 128, "source_bytes": 1048576}


def run_tests(workspace: Path, targets: list[str]) -> dict:
    if not isolation_available()["available"]:
        raise RuntimeError("Act requires privileged Linux namespaces; no fallback")
    helpers = {name: shutil.which(name) for name in ("unshare", "chroot", "mount", "setpriv", "mkdir", "touch")}
    if not all(helpers.values()) or not Path(PYTHON).is_file():
        raise RuntimeError("Act runtime helpers unavailable")
    if targets not in (["test_reproducer.py"], ["test_reproducer.py", "tests"], ["tests"]):
        raise ValueError("Unapproved test argv")
    workspace = workspace.resolve(strict=True)
    files = list(workspace.rglob("*"))
    if len(files) > LIMITS["source_files"]:
        raise ValueError("Source file cap exceeded")
    for path in files:
        if path.is_symlink() or (path.is_file() and path.stat().st_nlink != 1):
            raise ValueError("Workspace links rejected")
        if not (path.is_file() or path.is_dir()):
            raise ValueError("Special files rejected")
    if sum(p.stat().st_size for p in files if p.is_file()) > LIMITS["source_bytes"]:
        raise ValueError("Source byte cap exceeded")
    if any(workspace == Path(p) or Path(p) in workspace.parents for p in ("/usr", "/lib", "/bin")):
        raise ValueError("Source must be outside system runtime mounts")
    argv = [PYTHON, "-I", "-B", "/runner.py", "-q", "--tb=short", "-p", "no:cacheprovider",
            "-o", "pythonpath=/workspace", *targets]
    with tempfile.TemporaryDirectory(prefix="steward-act-jail-") as temporary:
        jail = Path(temporary) / "root"
        jail.mkdir(mode=0o755)
        # chroot starts in /; this controller-owned bootstrap selects cwd without
        # turning the configured argv into a shell command.
        bootstrap = '''import os, sys, json
os.chdir('/workspace')
import pytest
assert pytest.__version__ == '9.1.1', 'Pinned pytest runtime mismatch'
class Evidence:
    def __init__(self):
        self.calls = []
    @pytest.hookimpl(hookwrapper=True)
    def pytest_runtest_makereport(self, item, call):
        outcome = yield
        report = outcome.get_result()
        if call.when == 'call':
            self.calls.append({'nodeid': report.nodeid, 'outcome': report.outcome,
                               'exception': call.excinfo.type.__name__ if call.excinfo else None,
                               'xfail': hasattr(report, 'wasxfail')})
    def pytest_sessionfinish(self, session, exitstatus):
        print('STEWARD_TEST_REPORT=' + json.dumps({'calls': self.calls, 'collected': session.testscollected, 'exitstatus': int(exitstatus)}))
raise SystemExit(pytest.main(sys.argv[1:], plugins=[Evidence()]))
'''
        (jail / "runner.py").write_text(bootstrap, encoding="utf-8")
        wrapper = Path(temporary) / "enter.sh"
        q = shlex.quote
        lines = ["#!/bin/bash", "set -eu", f"{q(helpers['mount'])} --make-rprivate /",
                 "ulimit -c 0", "ulimit -t 5", "ulimit -v 262144", "ulimit -u 1", "ulimit -n 64", "ulimit -f 16384",
                 f"ROOT={q(str(jail))}", f"MOUNT={q(helpers['mount'])}", f"MKDIR={q(helpers['mkdir'])}",
                 '$MKDIR -p "$ROOT"/{workspace,tmp,proc,dev,usr,lib,lib64,bin,etc}',
                 'for d in /usr /lib /lib64 /bin; do',
                 'if [ -d "$d" ]; then $MKDIR -p "$ROOT$d"; $MOUNT --bind "$d" "$ROOT$d"; $MOUNT -o remount,ro,bind "$ROOT$d"; fi', 'done',
                 f'{q(helpers["touch"])} "$ROOT/dev/null"', '$MOUNT --bind /dev/null "$ROOT/dev/null"',
                 '$MOUNT -t tmpfs -o size=8m,nr_inodes=256,mode=1777,nosuid,nodev tmpfs "$ROOT/tmp"',
                 '$MOUNT -t proc -o nosuid,nodev,noexec proc "$ROOT/proc"',
                 f'$MOUNT --bind {q(str(workspace))} "$ROOT/workspace"',
                 '$MOUNT -o remount,ro,bind "$ROOT/workspace"',
                 # Change directory before chroot; -I suppresses ambient Python paths.
                 'cd "$ROOT/workspace"',
                 f'exec {q(helpers["chroot"])} "$ROOT" {q(helpers["setpriv"])} --reuid=65534 --regid=65534 --clear-groups --no-new-privs --bounding-set=-all -- ' + shlex.join(argv)]
        wrapper.write_text("\n".join(lines)+"\n", encoding="utf-8")
        wrapper.chmod(0o755)
        env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8", "HOME": "/tmp", "TMPDIR": "/tmp",
               "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1", "PYTHONDONTWRITEBYTECODE": "1"}
        command = [helpers["unshare"], "--mount", "--net", "--pid", "--fork", "--kill-child=KILL", str(wrapper)]
        proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=env, start_new_session=True)
        output = bytearray()
        reason = None
        deadline = time.monotonic() + LIMITS["wall_seconds"]
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(proc.stdout, selectors.EVENT_READ)
                while selector.get_map():
                    left = deadline - time.monotonic()
                    if left <= 0:
                        reason = "wall_limit"
                        break
                    for key, _ in selector.select(min(left, 0.1)):
                        chunk = os.read(key.fileobj.fileno(), 4096)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            continue
                        room = LIMITS["output_bytes"] - len(output)
                        output.extend(chunk[:room])
                        if len(chunk) > room:
                            reason = "output_limit"
                            break
                    if reason:
                        break
            if reason is None:
                proc.wait(timeout=max(0.01, deadline-time.monotonic()))
        except subprocess.TimeoutExpired:
            reason = "wall_limit"
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            proc.wait()
            proc.stdout.close()
        text = output.decode("utf-8", errors="replace")
        reports = [line.split("STEWARD_TEST_REPORT=", 1)[1] for line in text.splitlines() if "STEWARD_TEST_REPORT=" in line]
        report = None
        if len(reports) == 1:
            try:
                report = json.loads(reports[0])
            except ValueError:
                pass
        return {"returncode": proc.returncode, "output": text, "controller_report": report,
                "limit_reason": reason, "limits": LIMITS, "helpers": helpers, "argv": argv,
                "network": "isolated", "source_mount": "read-only", "uid": 65534}
