"""Adversarial: filesystem escape attempts from agent workspace."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from descend.sandbox import Workspace, assert_path_inside, ControllerRoots


def test_path_traversal_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp, "run1")
        with pytest.raises(PermissionError):
            ws.path("../secret")
        with pytest.raises(PermissionError):
            ws.path("../../etc/passwd")
        with pytest.raises(PermissionError):
            ws.path("scratch/../../outside")


def test_absolute_path_rejected():
    with tempfile.TemporaryDirectory() as tmp:
        ws = Workspace(tmp, "run1")
        with pytest.raises(PermissionError):
            ws.path("/etc/passwd")
        with pytest.raises(PermissionError):
            ws.path("/tmp/evil")


def test_assert_path_inside_blocks_escape():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "ws"
        root.mkdir()
        with pytest.raises(PermissionError):
            assert_path_inside(root, Path("../x"))
        with pytest.raises(PermissionError):
            assert_path_inside(root, Path("/tmp"))


def test_symlink_to_controller_not_followed_for_write():
    """Creating a symlink inside workspace that points outside must not allow write escape."""
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        agent_root = base / "agent"
        ctrl = ControllerRoots(base / "controller")
        secret = ctrl.config / "promotion.yaml"
        secret.write_text("secret: true", encoding="utf-8")

        ws = Workspace(agent_root, "run1")
        link = ws.root / "scratch" / "escape_link"
        try:
            link.symlink_to(secret)
        except OSError:
            pytest.skip("symlink not permitted in this environment")

        # Writing via workspace API using the link name should still be confined
        # because path() resolves and checks containment. If resolve escapes, PermissionError.
        with pytest.raises(PermissionError):
            # relative path that resolves outside via symlink
            ws.write("scratch/escape_link", "pwned")


def test_controller_roots_separate_from_agent():
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        agent = base / "agent_ws"
        ctrl = ControllerRoots(base / "ctrl")
        agent.mkdir()
        # Paths must not overlap
        assert not str(ctrl.registry).startswith(str(agent.resolve()))
        assert not str(ctrl.hidden).startswith(str(agent.resolve()))
        assert (base / "ctrl" / "registry").is_dir()
