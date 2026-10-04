"""Build Arm A manifest (common ops + target evidence)."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .schema import OPERATIONAL_KEYS, TARGET_EVIDENCE_KEYS


def default_operational(
    budgets: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Common operating information given to both A and B."""
    budgets = budgets or {}
    return {
        "tool_documentation": {
            "build_dataset": "Request generation of training examples from permitted classes only.",
            "dev_eval": "Evaluate a candidate on the development set (budgeted).",
            "submit_training": "Submit a LoRA training job (budgeted).",
            "commit_candidate": "Commit a final candidate adapter (irreversible).",
            "commit_prediction": "Commit predictions and intervals before hidden eval (irreversible).",
            "read_registry": "Read-only view of this run's registry events.",
        },
        "allowed_actions": [
            "build_dataset",
            "dev_eval",
            "submit_training",
            "commit_candidate",
            "commit_prediction",
            "read_registry",
        ],
        "data_generator_limits": {"max_examples_total": 100, "allowed_depths": [1, 2]},
        "budget_counters": {
            "dev_evals_used": budgets.get("dev_evals_used", 0),
            "dev_evals_max": budgets.get("dev_evals_max", 5),
            "training_submissions_used": budgets.get("training_submissions_used", 0),
            "training_submissions_max": budgets.get("training_submissions_max", 3),
            "actions_used": budgets.get("actions_used", 0),
            "actions_max": budgets.get("actions_max", 50),
        },
        "wall_clock_budget_sec": budgets.get("wall_clock_budget_sec", 3600),
        "agent_token_budget": budgets.get("agent_token_budget", 100_000),
        "training_submission_budget": budgets.get("training_submissions_max", 3),
        "dev_evaluation_budget": budgets.get("dev_evals_max", 5),
        "max_training_tokens": budgets.get("max_training_tokens", 50_000),
        "editable_surfaces": ["scratch/", "datasets/", "configs/", "notes/"],
        "sandbox_restrictions": [
            "No raw credentials",
            "No unrestricted network",
            "No access to controller internals",
            "No access to hidden examples or seeds",
        ],
        "candidate_commit_rules": (
            "Candidate commit is irreversible. After commit the adapter artifact "
            "and its identity hash are frozen."
        ),
        "prediction_commit_rules": (
            "Prediction commit is irreversible and required before hidden evaluation. "
            "Must include predicted_target_delta, interval_low, interval_high, "
            "predicted_regression_deltas, and rationale."
        ),
    }


def build_arm_a_manifest(
    *,
    target_evidence: Dict[str, Any],
    budgets: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Arm A = common operating information + target-specific evidence.
    """
    ops = default_operational(budgets)
    # Ensure only allowed target keys
    evidence = {k: v for k, v in target_evidence.items() if k in TARGET_EVIDENCE_KEYS}
    return {
        "arm": "A",
        "operational": ops,
        "target_evidence": evidence,
    }
