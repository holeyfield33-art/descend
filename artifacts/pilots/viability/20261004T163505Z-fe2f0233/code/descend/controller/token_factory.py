"""Offline controller request preparation adapted from the official cookbook.

No client, credentials, network calls or cookbook imports. See
docs/TOKEN_FACTORY_REFERENCE.md and docs/PROVENANCE.md for pinned sources.
"""
from __future__ import annotations

import json
import math
from typing import Any

INFERENCE_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
CONTROL_PLANE_BASE_URL = "https://api.tokenfactory.nebius.com"
TERMINAL_JOB_STATUSES = frozenset({"succeeded", "failed", "cancelled"})


def _identifier(value: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError("nonempty identifier required")
    return value


def chat_request(*, model: str, messages: list[dict[str, Any]], max_tokens: int,
                 tools: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Prepare kwargs for the cookbook's client.chat.completions.create call."""
    if type(max_tokens) is not int or max_tokens <= 0:
        raise ValueError("positive output cap required")
    if not isinstance(messages, list) or not messages:
        raise ValueError("messages required")
    body = {"model": _identifier(model), "messages": messages, "max_tokens": max_tokens}
    if tools is not None:
        body.update(tools=tools, tool_choice="auto")
    return json.loads(json.dumps(body, allow_nan=False))


def tool_request(call: dict[str, Any], *, allowed_tools: set[str]) -> dict[str, Any]:
    """Decode a provider function call into the existing ToolSession envelope.

    The caller supplies controller-owned tool names. Dispatch still validates
    arguments, the run binding, state transitions and budgets independently.
    """
    if call.get("type") != "function":
        raise ValueError("function call required")
    function = call.get("function")
    if not isinstance(function, dict) or function.get("name") not in allowed_tools:
        raise ValueError("tool not allowed")
    arguments = function.get("arguments")
    if not isinstance(arguments, str) or len(arguments.encode("utf-8")) > 65536:
        raise ValueError("invalid tool arguments")
    args = json.loads(arguments)
    if not isinstance(args, dict):
        raise ValueError("tool arguments must be an object")
    return {"tool": function["name"], "args": args}


def fine_tuning_request(*, model: str, training_file: str, n_epochs: int,
                        learning_rate: float, seed: int, lora_r: int = 8,
                        validation_file: str | None = None) -> dict[str, Any]:
    """Prepare the documented LoRA JSON body; never submit a job."""
    if type(n_epochs) is not int or not 1 <= n_epochs <= 20:
        raise ValueError("invalid epoch count")
    if type(learning_rate) not in (int, float) or not math.isfinite(learning_rate) or learning_rate < 0:
        raise ValueError("invalid learning rate")
    if type(seed) is not int or type(lora_r) is not int or not 8 <= lora_r <= 128:
        raise ValueError("invalid seed or LoRA rank")
    body = {"model": _identifier(model), "training_file": _identifier(training_file),
            "seed": seed, "hyperparameters": {"n_epochs": n_epochs,
            "learning_rate": learning_rate, "lora": True, "lora_r": lora_r}}
    if validation_file is not None:
        body["validation_file"] = _identifier(validation_file)
    return body


def job_finished(status: str) -> bool:
    """Terminal states are finished; queued/running states need polling."""
    return status in TERMINAL_JOB_STATUSES
