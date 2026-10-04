import json
import time
import pytest
from descend.controller import Controller, BudgetState, BudgetExhausted
from descend.dsl import generate_dsl, make_splits
from descend.sandbox.transport import ToolSession


@pytest.fixture
def run(tmp_path):
    c = Controller(workspace_root=tmp_path / "agent", controller_root=tmp_path / "controller")
    start = c.start_run("A", 42)
    return c, start["run_id"]


def commit(c, r):
    ds = c.create_dataset(r, [{"input": "a", "output": "a"}])
    c.submit_training(r, ds["dataset_hash"], {"epochs": 1})
    c.commit_candidate(r)
    pred = {"predicted_target_delta": 0.15, "interval_low": 0.05, "interval_high": 0.3,
            "predicted_regression_deltas": {"reg_shallow": -0.01}, "rationale": "test"}
    c.commit_prediction(r, pred)
    return pred


def test_decision_reads_frozen_prediction(run):
    c, r = run
    pred = commit(c, r)
    pred["predicted_target_delta"] = 999
    c._runs[r].prediction["predicted_target_delta"] = 888
    c.hidden_eval(r)
    assert c.decide(r)["predicted_delta"] == 0.15


def test_contamination_only_flag_and_filtered_registry(run):
    c, r = run
    result = c.create_dataset(r, c._runs[r].splits.hidden[:1])
    assert result["contamination"] == {"passed": False}
    event = c.registry.events(r)[-1]
    assert event["payload"]["contamination"] == {"passed": False}
    commit(c, r)
    c.hidden_eval(r)
    view = json.dumps(c.registry.read_only_view(r))
    assert "hidden_accuracy" not in view and "hidden_eval" not in view
    assert "ngram_similarity" not in view and "exact_matches" not in view


def test_private_hidden_seed_changes_splits_and_pairs(run):
    c, r = run
    state = c._runs[r]
    reconstructed = make_splits(generate_dsl(42), split_seed=42)
    assert state.splits.hidden != reconstructed.hidden
    paired = c.start_run("B", 42)["run_id"]
    assert c._runs[paired].splits.hidden == state.splits.hidden
    assert str(state.hidden_seed) not in json.dumps(c.registry.read_only_view(r))
    other = c.start_run("A", 43)["run_id"]
    assert c._runs[other].hidden_seed != state.hidden_seed


@pytest.mark.parametrize("method", ["record_training", "record_dev_eval", "record_action"])
def test_zero_action_cap_blocks_all_actions(method):
    b = BudgetState(actions_max=0)
    with pytest.raises(BudgetExhausted):
        getattr(b, method)()
    assert b.actions_used == b.training_submissions_used == b.dev_evals_used == 0
    assert not b.respected()


def test_budget_overrun_rejects_committed_candidate(run):
    c, r = run
    commit(c, r)
    c._runs[r].budgets.actions_max = c._runs[r].budgets.actions_used
    with pytest.raises(BudgetExhausted):
        c._runs[r].budgets.record_action()
    c.hidden_eval(r)
    reasons = c.decide(r)["reasons"]
    assert next(x for x in reasons if x["criterion"] == "budgets_respected")["passed"] is False


def test_time_and_token_caps():
    b = BudgetState(wall_clock_budget_sec=1)
    b.started_at = time.monotonic() - 2
    with pytest.raises(BudgetExhausted):
        b.record_training()
    for training in (False, True):
        b = BudgetState(agent_token_budget=0, max_training_tokens=0)
        with pytest.raises(BudgetExhausted):
            b.record_tokens(1, training=training)


def test_narrow_dispatch_and_postcommit_closure(run):
    c, r = run
    session = ToolSession(c, r)
    for tool in ("hidden_eval", "decide", "start_run", "_require"):
        with pytest.raises(ValueError):
            session.dispatch({"tool": tool, "args": {}})
    with pytest.raises(ValueError):
        session.dispatch({"tool": "read_registry", "args": {"run_id": "other"}})
    commit(c, r)
    with pytest.raises(RuntimeError, match="closed"):
        c.create_dataset(r, [])
    c.hidden_eval(r)
    with pytest.raises(RuntimeError, match="closed"):
        c.read_registry(r)


def test_generation_and_training_bounds(run):
    c, r = run
    session = ToolSession(c, r)
    with pytest.raises(BudgetExhausted):
        session.dispatch({"tool": "build_dataset", "args": {"n_examples": 1, "max_depth": 3}})
    assert not c._runs[r].budgets.respected()


def test_controller_training_token_limit(run):
    c, r = run
    ds = c.create_dataset(r, [{"input": "abc", "output": "abc"}])
    c._runs[r].budgets.max_training_tokens = 5
    with pytest.raises(BudgetExhausted):
        c.submit_training(r, ds["dataset_hash"], {"epochs": 1})
    assert c._runs[r].candidate is None


def test_transport_generation_limit_is_cumulative(run):
    c, r = run
    session = ToolSession(c, r)
    session.dispatch({"tool": "build_dataset", "args": {"n_examples": 100, "max_depth": 1}})
    with pytest.raises(BudgetExhausted):
        session.dispatch({"tool": "build_dataset", "args": {"n_examples": 100, "max_depth": 1}})


def test_rejected_requests_consume_action_budget(run):
    c, r = run
    c._runs[r].budgets.actions_max = 1
    session = ToolSession(c, r)
    with pytest.raises(ValueError):
        session.dispatch({"tool": "evil", "args": {}})
    with pytest.raises(BudgetExhausted):
        session.dispatch({"tool": "evil", "args": {}})


def test_frozen_prediction_tamper_after_reveal_rejected(run):
    from pathlib import Path
    c, r = run
    commit(c, r)
    c.hidden_eval(r)
    path = Path(c._runs[r].prediction["_frozen_path"])
    pred = json.loads(path.read_text())
    pred["predicted_target_delta"] = 999
    path.write_text(json.dumps(pred))
    with pytest.raises(RuntimeError, match="TOCTOU"):
        c.decide(r)


def test_dev_feedback_cap_and_independence(run):
    c, r = run
    ds = c.create_dataset(r, [{"input": "a", "output": "a"}])
    c.submit_training(r, ds["dataset_hash"], {"epochs": 1})
    c._runs[r].budgets.dev_evals_max = 1
    c._runs[r].splits.hidden = None
    result = ToolSession(c, r).dispatch({"tool": "dev_eval", "args": {}})
    assert set(result) == {"dev_accuracy"}
    with pytest.raises(BudgetExhausted):
        c.dev_eval(r)


def test_generation_limit_survives_new_tool_session(run):
    c, r = run
    c.create_dataset(r, [{"input": "a", "output": "a"}] * 100)
    with pytest.raises(BudgetExhausted):
        ToolSession(c, r).dispatch({"tool": "build_dataset", "args": {"n_examples": 1, "max_depth": 1}})
