"""Adversarial: registry tampering and controller attack attempts."""

from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path

import pytest
from descend.sandbox.hard_isolation import isolation_available

from descend.controller import Controller, BudgetState
from descend.registry import RegistryStore, verify_chain
from descend.agents.fake_agent import FakeAgent


def test_registry_edit_previous_event_fails_verify():
    with tempfile.TemporaryDirectory() as tmp:
        store = RegistryStore(tmp)
        store.append("run_start", "r1", "A", 1, {"x": 1})
        store.append("manifest_issued", "r1", "A", 1, {"y": 2})
        path = Path(tmp) / "r1.jsonl"
        lines = path.read_text().strip().splitlines()
        ev = json.loads(lines[0])
        ev["payload"]["x"] = 999
        lines[0] = json.dumps(ev, sort_keys=True)
        path.write_text("\n".join(lines) + "\n")
        ok, err = store.verify("r1")
        assert not ok
        assert err is not None


def test_registry_delete_event_fails_verify():
    with tempfile.TemporaryDirectory() as tmp:
        store = RegistryStore(tmp)
        for i in range(3):
            store.append("dev_eval" if i else "run_start", "r1", "A", 1, {"i": i})
        path = Path(tmp) / "r1.jsonl"
        lines = path.read_text().strip().splitlines()
        path.write_text(lines[0] + "\n" + lines[2] + "\n")
        ok, err = store.verify("r1")
        assert not ok


def test_registry_truncate_detected():
    with tempfile.TemporaryDirectory() as tmp:
        store = RegistryStore(tmp)
        store.append("run_start", "r1", "A", 1, {"x": 1})
        store.append("run_end", "r1", "A", 1, {"x": 2})
        path = Path(tmp) / "r1.jsonl"
        path.write_text("")  # truncate
        events = store.events("r1")
        assert events == []
        # empty chain verifies, but experimental record is gone — verifier of
        # expected length would fail at analysis time; chain itself is valid empty
        ok, _ = store.verify("r1")
        assert ok  # empty is valid; higher-level audit must check expected events


@pytest.mark.skipif(not isolation_available()["available"],
                    reason="isolated fake worker requires Linux namespace privileges")
def test_cannot_hidden_eval_twice():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(Path(tmp) / "reg")
        ctl = Controller(registry=reg, workspace_root=Path(tmp) / "runs", controller_root=Path(tmp) / "ctrl")
        agent = FakeAgent()
        start = ctl.start_run("A", seed=200, budgets=BudgetState())
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 200)
        ctl.hidden_eval(run_id)
        with pytest.raises(RuntimeError, match="already"):
            ctl.hidden_eval(run_id)


def test_cannot_hidden_eval_before_commits():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(Path(tmp) / "reg")
        ctl = Controller(registry=reg, workspace_root=Path(tmp) / "runs", controller_root=Path(tmp) / "ctrl")
        start = ctl.start_run("A", seed=201, budgets=BudgetState())
        with pytest.raises(RuntimeError, match="committed"):
            ctl.hidden_eval(start["run_id"])


def test_agent_start_has_no_hidden_or_controller_paths():
    with tempfile.TemporaryDirectory() as tmp:
        ctl = Controller(
            registry=RegistryStore(Path(tmp) / "reg"),
            workspace_root=Path(tmp) / "runs",
            controller_root=Path(tmp) / "ctrl",
        )
        start = ctl.start_run("A", seed=202)
        blob = json.dumps(start)
        assert "hidden" not in start
        assert "splits" not in start
        assert str(ctl.roots.hidden) not in blob
        assert str(ctl.roots.registry) not in blob
