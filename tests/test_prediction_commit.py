"""Prediction and candidate commit protocol."""

from __future__ import annotations

import tempfile
import pytest
from descend.sandbox.hard_isolation import isolation_available

requires_worker = pytest.mark.skipif(not isolation_available()["available"],
                                    reason="isolated fake worker requires Linux namespace privileges")

from descend.controller import Controller, BudgetState
from descend.registry import RegistryStore
from descend.agents.fake_agent import FakeAgent


def test_hidden_eval_requires_commits():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        start = ctl.start_run("A", seed=50, budgets=BudgetState())
        run_id = start["run_id"]
        with pytest.raises(RuntimeError, match="committed candidate"):
            ctl.hidden_eval(run_id)


@requires_worker
def test_prediction_immutable():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        agent = FakeAgent()
        start = ctl.start_run("A", seed=51, budgets=BudgetState())
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 51)
        with pytest.raises(RuntimeError, match="already committed"):
            ctl.commit_prediction(run_id, {
                "predicted_target_delta": 0.99,
                "interval_low": 0,
                "interval_high": 1,
                "predicted_regression_deltas": {},
                "rationale": "tamper",
            })


@requires_worker
def test_candidate_immutable():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        agent = FakeAgent()
        start = ctl.start_run("A", seed=52, budgets=BudgetState())
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 52)
        with pytest.raises(RuntimeError, match="already committed"):
            ctl.commit_candidate(run_id)
