import json
import pytest
from descend.controller import Controller
from descend.agents.fake_agent import FakeAgent
from descend.sandbox.hard_isolation import isolation_available
from descend.sandbox.transport import run_isolated_agent


@pytest.fixture
def isolated(tmp_path):
    if not isolation_available()["available"]:
        pytest.skip("Linux namespace/chroot privileges required; no soft fallback")
    c = Controller(workspace_root=tmp_path / "agent", controller_root=tmp_path / "controller")
    start = c.start_run("A", 17)
    return c, start


def test_fake_worker_integrated_flow(isolated):
    c, start = isolated
    result = FakeAgent().run(start["manifest"], c, start["run_id"], 17)
    assert result["status"] == "completed"
    state = c._runs[start["run_id"]]
    assert state.candidate_committed and state.prediction_committed
    assert not state.hidden_eval_done
    assert state.transcript
    assert c.registry.verify(start["run_id"])[0]


def test_hostile_worker_and_approved_pipe(isolated, monkeypatch):
    c, start = isolated
    r = start["run_id"]
    sentinel = c.roots.hidden / "sentinel"
    sentinel.write_text("PRIVATE_CONTROLLER_SENTINEL")
    registry_path = c.registry._path(r)
    original = registry_path.read_bytes()
    monkeypatch.setenv("HF_TOKEN", "PRIVATE_TOKEN_SENTINEL")
    paths = [str(sentinel), str(registry_path), "/proc/1/root" + str(sentinel),
             "/workspace/../../" + str(sentinel).lstrip("/"),
             "/var/run/docker.sock", "/controller/config/promotion.yaml"]
    source = "PATHS=" + repr(paths) + "\n" + r'''
import os, json, socket, sys
results = {"uid": os.getuid(), "reads": [], "writes": [], "network": [],
           "env": dict(os.environ), "has_controller_object": "controller" in globals()}
for p in PATHS:
    try:
        with open(p, "rb") as f: results["reads"].append(f.read().decode(errors="replace"))
    except OSError: pass
    try:
        with open(p, "w") as f: f.write("EVIL")
        results["writes"].append(p)
    except OSError: pass
    try: os.unlink(p)
    except OSError: pass
try:
    os.symlink(PATHS[0], "/workspace/escape")
    results["reads"].append(open("/workspace/escape").read())
except OSError: pass
try:
    os.link(PATHS[0], "/workspace/hardlink")
    results["reads"].append(open("/workspace/hardlink").read())
except OSError: pass
for host in ("1.1.1.1", "127.0.0.1", "172.17.0.1", "169.254.169.254"):
    try:
        with socket.create_connection((host, 80), timeout=0.2): results["network"].append(host)
    except OSError: pass
try:
    socket.getaddrinfo("example.com", 443)
    results["network"].append("DNS")
except OSError: pass
for tool in ("hidden_eval", "decide", "_require", "start_run"):
    print(json.dumps({"tool": tool, "args": {}}), flush=True)
    assert json.loads(sys.stdin.readline())["ok"] is False
print(json.dumps({"tool": "build_dataset", "args": {"n_examples": 2, "max_depth": 1}}), flush=True)
response = json.loads(sys.stdin.readline())
assert response["ok"] and set(response["result"]["contamination"]) == {"passed"}
results["mediated_tool"] = True
print(json.dumps({"type": "result", "result": results}), flush=True)
'''
    result = run_isolated_agent(c, r, source)
    assert result["uid"] == 65534
    assert result["reads"] == result["writes"] == result["network"] == []
    assert "PRIVATE_TOKEN_SENTINEL" not in json.dumps(result["env"])
    assert not result["has_controller_object"] and result["mediated_tool"]
    assert sentinel.read_text() == "PRIVATE_CONTROLLER_SENTINEL"
    # Approved generation appends one event; old events remain intact.
    assert registry_path.read_bytes().startswith(original)
    assert c.registry.verify(r)[0]


def test_oversized_transport_request_fails_closed(isolated):
    c, start = isolated
    with pytest.raises(RuntimeError, match="no soft fallback"):
        run_isolated_agent(c, start["run_id"], 'print("x" * 70000, flush=True)')
    assert not c._runs[start["run_id"]].candidate_committed


def test_unavailable_runtime_never_executes_worker(tmp_path, monkeypatch):
    import descend.sandbox.hard_isolation as hard
    monkeypatch.setattr(hard, "isolation_available", lambda: {"available": False, "reason": "test"})
    marker = tmp_path / "evil"
    c = Controller(workspace_root=tmp_path / "agent", controller_root=tmp_path / "controller")
    start = c.start_run("A", 1)
    with pytest.raises(RuntimeError, match="no soft fallback"):
        run_isolated_agent(c, start["run_id"], f'open({str(marker)!r}, "w").write("evil")')
    assert not marker.exists()


def test_zero_action_cap_halts_integrated_worker(isolated):
    c, start = isolated
    state = c._runs[start["run_id"]]
    state.budgets.actions_max = 0
    with pytest.raises(RuntimeError, match="no soft fallback"):
        FakeAgent().run(start["manifest"], c, start["run_id"], 17)
    assert state.budgets.breached
    assert not state.datasets and not state.candidate_committed
