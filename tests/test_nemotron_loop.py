import json

import pytest

from descend.agents.nemotron import NemotronAgent
from descend.controller import Controller
from descend.registry import canonical_hash
from descend.sandbox.hard_isolation import isolation_available


class OfflineInference:
    def __init__(self):
        self.turn = 0

    def complete(self, messages, state, *, seed):
        self.turn += 1
        if self.turn > 1:
            status = json.loads(messages[-1]["content"])["operational_status"]
            assert status["generation_examples_remaining"] == 100 - state.generated_examples
            assert status["candidate_committed"] == state.candidate_committed
        dataset_hash = next(iter(state.datasets), "")
        actions = [
            ("build_dataset", {"n_examples": 16, "max_depth": 2}),
            ("submit_training", {"dataset_hash": dataset_hash, "config": {"epochs": 1, "lr": 0.0001}}),
            ("dev_eval", {}), ("commit_candidate", {}),
            ("commit_prediction", {"predicted_target_delta": 0, "interval_low": -1,
             "interval_high": 1, "predicted_regression_deltas": {"reg_shallow": 0}, "rationale": "test"}),
        ]
        message = {"role": "assistant", "content": None}
        if self.turn <= len(actions):
            tool, args = actions[self.turn - 1]
            message["tool_calls"] = [{"id": f"call-{self.turn}", "type": "function",
                                      "function": {"name": tool, "arguments": json.dumps(args)}}]
        else:
            message["content"] = "Done"
        return {"response": {"choices": [{"message": message}]}, "request": {"messages": messages},
                "reservation_id": "offline", "provider_tokens": 0, "accounted_upper_bound_usd": 0,
                "estimated_list_price_usd": 0}


@pytest.mark.skipif(not isolation_available()["available"], reason="Requires integrated Linux boundary")
def test_nemotron_tool_loop_uses_isolated_relay(tmp_path):
    controller = Controller(workspace_root=tmp_path / "runs", controller_root=tmp_path / "controller")
    start = controller.start_run("A", 42)
    inference = OfflineInference()
    result = NemotronAgent(inference, count_tokens=len).run(start["manifest"], controller, start["run_id"], 42)
    assert result == {"status": "completed", "turns": 6}
    state = controller._require(start["run_id"])
    assert state.candidate_committed and state.prediction_committed
    assert state.budgets.dev_evals_used == 1
    assert not state.hidden_eval_done
    controller.hidden_eval(start["run_id"])
    controller.decide(start["run_id"])
    assert controller.registry.verify(start["run_id"])[0]


def test_unsupported_host_never_calls_provider(tmp_path, monkeypatch):
    controller = Controller(workspace_root=tmp_path / "runs")
    start = controller.start_run("A", 42)
    inference = OfflineInference()
    monkeypatch.setattr("descend.agents.nemotron.isolation_available", lambda: {"available": False})
    with pytest.raises(RuntimeError, match="no provider call"):
        NemotronAgent(inference, count_tokens=len).run(start["manifest"], controller, start["run_id"], 42)
    assert inference.turn == 0
