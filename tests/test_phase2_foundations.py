import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace

import pytest

from descend.controller import Controller, BudgetState
from descend.controller.inference import TokenFactoryInference, ProviderFailure
from descend.controller.spend import SpendLedger, SpendExhausted
from descend.registry import RegistryStore


def test_truncated_valid_prefix_rejected_and_cannot_append(tmp_path):
    store = RegistryStore(tmp_path)
    store.append("run_start", "r", "A", 1, {})
    store.append("run_end", "r", "A", 1, {})
    path = store._path("r")
    path.write_text(path.read_text().splitlines()[0] + "\n")
    assert not store.verify("r")[0]
    with pytest.raises(RuntimeError, match="invalid registry"):
        store.append("dev_eval", "r", "A", 1, {})


def test_spend_restart_and_ambiguous_hold(tmp_path):
    path = tmp_path / "spend.db"
    ledger = SpendLedger(path, cap_micro_usd=100)
    hold = ledger.reserve("r", 60)
    again = SpendLedger(path, cap_micro_usd=100)
    with pytest.raises(SpendExhausted):
        again.reserve("r", 41)
    again.settle(hold, 30, "provider-id")
    assert ledger.summary()["accounted_upper_bound_usd"] == 30 / 1_000_000
    with pytest.raises(ValueError):
        SpendLedger(path, cap_micro_usd=101)


def test_parallel_spend_reservations_are_atomic(tmp_path):
    ledger = SpendLedger(tmp_path / "spend.db", cap_micro_usd=100)
    def reserve(_):
        try:
            ledger.reserve("r", 60)
            return True
        except SpendExhausted:
            return False
    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sum(pool.map(reserve, range(2))) == 1


def test_overrun_halts_future_calls(tmp_path):
    ledger = SpendLedger(tmp_path / "spend.db", cap_micro_usd=100)
    hold = ledger.reserve("r", 20)
    with pytest.raises(SpendExhausted):
        ledger.settle(hold, 21, "id")
    with pytest.raises(SpendExhausted):
        ledger.reserve("r", 1)


def test_b_matches_actual_a_report_not_dummy(tmp_path):
    c = Controller(workspace_root=tmp_path / "runs")
    a = c.start_run("A", 42)["manifest"]
    b = c.start_run("B", 42)["manifest"]
    assert len(b["neutral_content"]) == len(json.dumps(a["target_evidence"], sort_keys=True))
    assert a["operational"] == b["operational"]


def test_adapter_bytes_rechecked(tmp_path):
    c = Controller(workspace_root=tmp_path / "runs")
    r = c.start_run("A", 42)["run_id"]
    ds = c.create_dataset(r, [{"input": "a", "output": "a"}])
    c.submit_training(r, ds["dataset_hash"], {"epochs": 1})
    c.commit_candidate(r)
    c.commit_prediction(r, {"predicted_target_delta": 0, "interval_low": -1, "interval_high": 1,
                           "predicted_regression_deltas": {}, "rationale": "test"})
    Path(c._runs[r].candidate["_adapter_path"]).write_bytes(b"tampered")
    with pytest.raises(RuntimeError, match="adapter bytes"):
        c.hidden_eval(r)


def test_inference_charges_usage_and_retains_unknown_calls(tmp_path):
    ledger = SpendLedger(tmp_path / "spend.db")
    record = {"id": "id", "usage": {"prompt_tokens": 10, "completion_tokens": 20}, "choices": []}
    response = SimpleNamespace(model_dump=lambda **_: record)
    sent = []
    def create(**kwargs):
        sent.append(kwargs)
        return response
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))
    inference = TokenFactoryInference(api_key="offline", ledger=ledger, client=client)
    state = SimpleNamespace(run_id="r", budgets=BudgetState())
    inference.complete([{"role": "user", "content": "test"}], state, seed=1)
    assert sent[-1]["tool_choice"] == "auto"
    assert sent[-1]["extra_body"] == {"chat_template_kwargs": {"enable_thinking": False}}
    assert state.budgets.tokens_used == 30
    assert ledger.summary()["unresolved_calls"] == 0
    state.candidate_committed = state.prediction_committed = True
    inference.complete([{"role": "user", "content": "test"}], state, seed=1)
    assert sent[-1]["tool_choice"] == "none"
    record["usage"] = None
    with pytest.raises(ProviderFailure):
        inference.complete([{"role": "user", "content": "test"}], state, seed=1)
    assert ledger.summary()["unresolved_calls"] == 1
