"""Hard-boundary adversarial tests (Linux namespaces / unshare).

These tests only claim PASS when hard isolation is available on the host.
If unavailable, they skip with a clear reason (Claim B remains NOT YET PROVEN).
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import pytest

from descend.sandbox.hard_isolation import (
    isolation_available,
    run_in_hard_isolation,
    probe_script,
    mock_tool_proxy_echo,
    NOBODY_UID,
)
from descend.sandbox.isolation import ControllerRoots


@pytest.fixture
def hard_env():
    avail = isolation_available()
    if not avail["available"]:
        pytest.skip(f"hard isolation unavailable: {avail}")
    with tempfile.TemporaryDirectory() as tmp:
        base = Path(tmp)
        workspace = base / "agent" / "workspace"
        workspace.mkdir(parents=True)
        ctrl = ControllerRoots(base / "controller")
        # Plant secrets and hidden data in controller (must NOT leak)
        (ctrl.config / "promotion.yaml").write_text("secret_threshold: 0.99\n", encoding="utf-8")
        (ctrl.hidden / "hidden_seed.txt").write_text("SEED=99999\n", encoding="utf-8")
        (ctrl.registry / "r1.jsonl").write_text('{"event":"run_start"}\n', encoding="utf-8")
        (ctrl.committed / "adapter.bin").write_text("ADAPTER_BYTES", encoding="utf-8")
        os.environ["NEBIUS_API_KEY"] = "should-never-appear-in-agent"
        os.environ["HF_TOKEN"] = "should-never-appear-in-agent"
        os.environ["DESCEND_CONTROLLER_ROOT"] = str(ctrl.base)
        try:
            yield {"workspace": workspace, "controller": ctrl, "avail": avail}
        finally:
            os.environ.pop("NEBIUS_API_KEY", None)
            os.environ.pop("HF_TOKEN", None)
            os.environ.pop("DESCEND_CONTROLLER_ROOT", None)


def _run_probe(hard_env):
    result = run_in_hard_isolation(
        probe_script(),
        workspace=hard_env["workspace"],
        controller_root=hard_env["controller"].base,
        timeout_sec=20,
    )
    assert not result.get("timed_out"), result
    # Parse last JSON line from stdout
    lines = [ln for ln in (result.get("stdout") or "").splitlines() if ln.strip().startswith("{")]
    assert lines, f"no JSON probe output: {result}"
    data = json.loads(lines[-1])
    return result, data


def test_hard_isolation_available_or_skip():
    info = isolation_available()
    assert "available" in info
    assert "runtime" in info


def test_agent_uid_is_not_root(hard_env):
    _, data = _run_probe(hard_env)
    assert data["uid"] == NOBODY_UID, data
    assert data["euid"] == NOBODY_UID, data


def test_no_secret_env_in_agent(hard_env):
    _, data = _run_probe(hard_env)
    assert data["secret_env"] == [], f"secrets leaked: {data['secret_env']}"
    assert data["has_controller_env"] is False


def test_network_egress_blocked(hard_env):
    _, data = _run_probe(hard_env)
    assert str(data["network_tcp"]).startswith("BLOCKED"), data["network_tcp"]
    assert str(data["network_dns"]).startswith("BLOCKED"), data["network_dns"]


def test_controller_paths_absent_from_agent_namespace(hard_env):
    _, data = _run_probe(hard_env)
    # Host controller paths must not exist inside the agent namespace
    assert data.get("found_controller_paths", []) == [], data.get("found_controller_paths")
    # Minimal root only
    root = set(data.get("list_root", []))
    forbidden = {"home", "root", "var", "run"}
    assert not (root & forbidden), f"host dirs still visible: {root & forbidden}"


def test_registry_backing_store_not_in_agent(hard_env):
    _, data = _run_probe(hard_env)
    reg = str(hard_env["controller"].registry)
    assert reg not in data.get("found_controller_paths", [])
    # Agent cannot unlink host registry — file still exists on host
    assert (hard_env["controller"].registry / "r1.jsonl").is_file()


def test_committed_artifacts_not_in_agent(hard_env):
    _, data = _run_probe(hard_env)
    committed = str(hard_env["controller"].committed)
    assert committed not in data.get("found_controller_paths", [])
    assert (hard_env["controller"].committed / "adapter.bin").read_text() == "ADAPTER_BYTES"


def test_approved_tool_proxy_still_works(hard_env):
    """Controller-mediated tool works outside the namespace (controlled action)."""
    resp = mock_tool_proxy_echo({"tool": "echo", "payload": {"hello": "world"}})
    assert resp["status"] == "ok"
    assert resp["mediated_by"] == "controller"
    assert resp["echo"]["hello"] == "world"


def test_workspace_is_writable(hard_env):
    _, data = _run_probe(hard_env)
    assert data.get("workspace_writable") is True


def test_pid_namespace_limits_visibility(hard_env):
    _, data = _run_probe(hard_env)
    # In a new PID namespace, /proc/1/environ is the agent's init, not the host controller.
    # Reading may succeed but should not contain host secrets.
    # If we cannot read it, that is also fine.
    if data.get("can_see_pid1_environ"):
        # environ of pid1 inside agent ns should not contain our planted secrets
        # (we didn't put secrets into agent env)
        assert data.get("secret_env") == []
