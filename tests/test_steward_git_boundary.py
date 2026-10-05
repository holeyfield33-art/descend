"""Git boundary contracts: hostile configuration is data, never a helper launch."""
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from descend.steward import watch
from descend.sandbox.hard_isolation import isolation_available, run_in_hard_isolation


@pytest.mark.parametrize("root_commit", [False, True])
def test_all_snapshot_git_calls_are_controller_owned(tmp_path, monkeypatch, root_commit):
    calls = []
    monkeypatch.setenv("NEBIUS_API_KEY", "test-only-sentinel")
    monkeypatch.setenv("GIT_CONFIG_COUNT", "1")
    monkeypatch.setenv("GIT_CONFIG_KEY_0", "diff.evil.textconv")
    monkeypatch.setenv("GIT_CONFIG_VALUE_0", "untrusted-helper")
    monkeypatch.setenv("GIT_DIR", "/unexpected")

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        args = argv[argv.index("-C") + 2:]
        if args == ["rev-parse", "--show-toplevel"]:
            result = str(tmp_path).encode()
        elif args == ["rev-parse", "HEAD"]:
            result = b"a" * 40
        elif args[0] == "rev-list":
            result = b"a" * 40 + (b"" if root_commit else b" " + b"b" * 40)
        elif "--name-only" in args:
            result = b"app.py\n"
        else:
            result = b"diff --git a/app.py b/app.py\n--- a/app.py\n+++ b/app.py\n@@ -0,0 +1 @@\n+x = 1\n"
        return SimpleNamespace(stdout=result)

    monkeypatch.setattr(watch.subprocess, "run", run)
    assert watch.commit_snapshot(tmp_path)["status"] == "ready"
    assert len(calls) == 5
    for argv, kwargs in calls:
        assert Path(argv[0]).is_absolute()
        assert "core.fsmonitor=false" in argv
        assert "protocol.allow=never" in argv
        assert "--no-replace-objects" in argv
        env = kwargs["env"]
        assert "NEBIUS_API_KEY" not in env
        assert not any(k.startswith("GIT_CONFIG_KEY") for k in env)
        assert "GIT_DIR" not in env
        assert env["GIT_NO_LAZY_FETCH"] == "1"
        assert env["GIT_CONFIG_GLOBAL"] == os.devnull
        if any(cmd in argv for cmd in ("diff", "diff-tree", "show")):
            assert "--no-ext-diff" in argv
            assert "--no-textconv" in argv
            assert "--ignore-submodules=all" in argv


def test_missing_git_fails_closed(tmp_path, monkeypatch):
    monkeypatch.setattr(watch, "GIT_EXECUTABLE", None)
    with pytest.raises(RuntimeError, match="Git executable unavailable"):
        watch.commit_snapshot(tmp_path)


@pytest.mark.skipif(not isolation_available()["available"], reason="Git helper execution probe requires Linux namespace worker")
def test_configured_textconv_never_executes_during_scan(tmp_path):
    workspace = tmp_path / "agent" / "workspace"
    workspace.mkdir(parents=True)
    (workspace / "watch.py").write_bytes(Path(watch.__file__).read_bytes())
    source = r'''
import json, os, subprocess
from pathlib import Path
from watch import commit_snapshot, ReviewStore, scan_once
root = Path('/workspace/repo')
root.mkdir()
def git(*args):
    result = subprocess.run(['/usr/bin/git', '-C', str(root), *args], capture_output=True)
    assert result.returncode == 0, (args, result.stderr.decode())
    return result
git('init')
git('config', 'user.name', 'Fixture')
git('config', 'user.email', 'fixture@example.invalid')
git('config', 'core.hooksPath', '/dev/null')
helper = Path('/workspace/helper.sh')
# Write literal newlines without depending on host line endings.
helper.write_text('#!/bin/sh' + chr(10) + 'printf invoked > /workspace/helper-invoked' + chr(10) + 'cat "$1"' + chr(10))
helper.chmod(0o755)
git('config', 'diff.fixture.textconv', str(helper))
(root / '.gitattributes').write_text('*.py diff=fixture' + chr(10))
(root / 'app.py').write_text('x = 1' + chr(10))
git('add', '.')
git('commit', '-m', 'root fixture')
marker = Path('/workspace/helper-invoked')
git('show', '--textconv', 'HEAD', '--', 'app.py')
assert marker.exists(), 'positive control did not execute configured helper'
marker.unlink()
for value in (1, 2):
    if value == 2:
        (root / 'app.py').write_text('x = 2' + chr(10))
        git('add', 'app.py')
        git('commit', '-m', 'second fixture')
    result = commit_snapshot(root)
    assert result['status'] == 'ready', result
    assert '+x = ' + str(value) in result['diff']
    for mode in ('mock', 'live-canned'):
        store = ReviewStore('/workspace/' + mode + '.sqlite')
        result = scan_once(root, store, lambda snapshot: {'content': 'canned, no provider'})
        assert result['status'] == 'reviewed', result
    assert not marker.exists(), 'scan executed configured helper'
print(json.dumps({'root_and_parent': True, 'helper_blocked': True, 'provider_calls': 0}))
'''
    result = run_in_hard_isolation(source, workspace=workspace, controller_root=tmp_path / "controller")
    assert result["ok"], result
    assert '"helper_blocked": true' in result["stdout"]
