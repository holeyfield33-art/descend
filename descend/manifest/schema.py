"""Manifest schema notes for Arm A / Arm B."""

from __future__ import annotations

# Operational (common to A and B) fields that must always be present
OPERATIONAL_KEYS = frozenset({
    "tool_documentation",
    "allowed_actions",
    "budget_counters",
    "wall_clock_budget_sec",
    "agent_token_budget",
    "training_submission_budget",
    "dev_evaluation_budget",
    "max_training_tokens",
    "editable_surfaces",
    "sandbox_restrictions",
    "candidate_commit_rules",
    "prediction_commit_rules",
})

# Target-specific evidence (Arm A only)
TARGET_EVIDENCE_KEYS = frozenset({
    "target_checkpoint_id",
    "target_checkpoint_hash",
    "architecture",
    "parameter_count",
    "tokenizer_characteristics",
    "adapter_compatibility",
    "baseline_capability_profile",
    "baseline_failure_profile",
    "modification_lineage",
})
