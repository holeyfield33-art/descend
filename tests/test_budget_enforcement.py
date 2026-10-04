"""Budget caps are enforced."""

from __future__ import annotations

import tempfile
import pytest

from descend.controller import Controller, BudgetState, BudgetExhausted
from descend.registry import RegistryStore


def test_dev_eval_cap():
    budgets = BudgetState(dev_evals_max=2)
    budgets.record_dev_eval()
    budgets.record_dev_eval()
    with pytest.raises(BudgetExhausted):
        budgets.record_dev_eval()


def test_training_cap():
    budgets = BudgetState(training_submissions_max=1)
    budgets.record_training()
    with pytest.raises(BudgetExhausted):
        budgets.record_training()


def test_action_cap():
    budgets = BudgetState(actions_max=2)
    budgets.record_action()
    budgets.record_action()
    with pytest.raises(BudgetExhausted):
        budgets.record_action()


def test_controller_training_budget():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        budgets = BudgetState(training_submissions_max=1, actions_max=20)
        start = ctl.start_run("A", seed=5, budgets=budgets)
        run_id = start["run_id"]
        ds = ctl.create_dataset(run_id, [{"input": "a", "output": "a"}])
        ctl.submit_training(run_id, ds["dataset_hash"], {"epochs": 1})
        with pytest.raises(BudgetExhausted):
            ctl.submit_training(run_id, ds["dataset_hash"], {"epochs": 1})
