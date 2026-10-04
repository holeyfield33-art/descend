"""Arm C: fixed scripted LoRA training recipe (no agent)."""

from __future__ import annotations

from typing import Any, Dict

from descend.tools.build_dataset import build_dataset_from_policy


def run_scripted_lora(controller: Any, run_id: str, seed: int) -> Dict[str, Any]:
    """Deterministic scripted baseline."""
    examples = build_dataset_from_policy(seed=seed, n_examples=32, max_depth=2)
    ds = controller.create_dataset(run_id, examples, source="scripted")
    config = {"epochs": 2, "lr": 2e-4, "recipe": "scripted_lora_v0"}
    train = controller.submit_training(run_id, ds["dataset_hash"], config)
    if train.get("status") != "success":
        return {"status": "train_failed"}
    identity = controller.commit_candidate(run_id)
    pred = {
        "predicted_target_delta": 0.10,
        "interval_low": 0.0,
        "interval_high": 0.25,
        "predicted_regression_deltas": {"reg_shallow": 0.0},
        "rationale": "Scripted baseline expects small positive transfer.",
    }
    controller.commit_prediction(run_id, pred)
    return {"status": "completed", "identity": identity}
