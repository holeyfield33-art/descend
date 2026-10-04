"""End-to-end CPU fake-agent flow."""

from __future__ import annotations

import tempfile
import pytest
from descend.sandbox.hard_isolation import isolation_available

pytestmark = pytest.mark.skipif(not isolation_available()["available"],
                               reason="isolated fake worker requires Linux namespace privileges")

from descend.controller import Controller, BudgetState
from descend.registry import RegistryStore
from descend.agents.fake_agent import FakeAgent


def test_full_success_flow():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        agent = FakeAgent(behavior="success")
        start = ctl.start_run("A", seed=100, budgets=BudgetState())
        run_id = start["run_id"]
        result = agent.run(start["manifest"], ctl, run_id, 100)
        assert result["status"] == "completed"

        hidden = ctl.hidden_eval(run_id)
        assert "target_delta" in hidden

        decision = ctl.decide(run_id)
        assert decision["decision"] in ("PROMOTE", "REJECT")

        ok, err = reg.verify(run_id)
        assert ok, err

        types = [e["event_type"] for e in reg.events(run_id)]
        assert "run_start" in types
        assert "manifest_issued" in types
        assert "dataset_created" in types
        assert "training_submitted" in types
        assert "candidate_committed" in types
        assert "prediction_committed" in types
        assert "hidden_eval" in types
        assert "decision" in types
        assert "run_end" in types


def test_failure_zero_gain():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        agent = FakeAgent(behavior="fail_train")
        start = ctl.start_run("A", seed=101, budgets=BudgetState())
        run_id = start["run_id"]
        result = agent.run(start["manifest"], ctl, run_id, 101)
        assert result["status"] == "train_failed"
        decision = ctl.decide(run_id)
        assert decision["decision"] == "REJECT"
        ok, _ = reg.verify(run_id)
        assert ok


def test_arm_b_flow():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        agent = FakeAgent()
        start = ctl.start_run("B", seed=102, budgets=BudgetState())
        assert start["manifest"]["arm"] == "B"
        assert "neutral_content" in start["manifest"]
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 102)
        ctl.hidden_eval(run_id)
        decision = ctl.decide(run_id)
        assert decision["decision"] in ("PROMOTE", "REJECT")
        ok, _ = reg.verify(run_id)
        assert ok
