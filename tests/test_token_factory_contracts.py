import pytest
from descend.controller.token_factory import chat_request, fine_tuning_request, job_finished, tool_request
from descend.sandbox.transport import ToolSession
from descend.controller import Controller


def test_provider_tool_calls_use_run_scoped_dispatch(tmp_path):
    c = Controller(workspace_root=tmp_path / "runs", controller_root=tmp_path / "controller")
    run = c.start_run("A", 3)["run_id"]
    call = {"id": "call-1", "type": "function", "function": {
        "name": "build_dataset", "arguments": '{"n_examples": 2, "max_depth": 1}'}}
    request = tool_request(call, allowed_tools={"build_dataset"})
    result = ToolSession(c, run).dispatch(request)
    assert set(result) == {"dataset_hash", "contamination"}
    call["function"]["name"] = "hidden_eval"
    with pytest.raises(ValueError, match="not allowed"):
        tool_request(call, allowed_tools={"build_dataset"})


def test_inference_payload_has_output_cap_and_detaches_input():
    messages = [{"role": "user", "content": "DSL task"}]
    body = chat_request(model="controller-selected-model", messages=messages, max_tokens=64)
    messages[0]["content"] = "changed"
    assert body["messages"][0]["content"] == "DSL task"
    assert body["max_tokens"] == 64
    with pytest.raises(ValueError):
        chat_request(model="m", messages=messages, max_tokens=0)


def test_fine_tuning_body_uses_current_rate_and_optional_validation():
    body = fine_tuning_request(model="controller-selected-target", training_file="file-train",
                               n_epochs=1, learning_rate=0.00001, seed=42)
    assert "validation_file" not in body and "integrations" not in body
    assert body["hyperparameters"]["learning_rate"] == 0.00001
    assert "learning_rate_multiplier" not in body["hyperparameters"]
    assert body["hyperparameters"]["lora"] is True
    with pytest.raises(ValueError):
        fine_tuning_request(model="m", training_file="f", n_epochs=0, learning_rate=1e-5, seed=1)


@pytest.mark.parametrize("status,done", [("running", False), ("queued", False),
                                        ("succeeded", True), ("failed", True), ("cancelled", True)])
def test_polling_does_not_invert_terminal_statuses(status, done):
    assert job_finished(status) is done
