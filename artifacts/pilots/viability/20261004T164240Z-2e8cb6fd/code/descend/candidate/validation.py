"""Candidate artifact validation for the CPU-first harness."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple


def validate_candidate(candidate: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Check structural validity of a candidate artifact.

    Returns (is_valid, list_of_reasons).
    """
    reasons: List[str] = []
    required = ["adapter_id", "adapter_hash", "training_dataset_hash", "training_config"]
    for key in required:
        if key not in candidate:
            reasons.append(f"missing required field: {key}")

    if "adapter_hash" in candidate:
        h = candidate["adapter_hash"]
        if not isinstance(h, str) or len(h) != 64:
            reasons.append("adapter_hash must be 64-char hex SHA-256")

    if candidate.get("status") == "invalid":
        reasons.append("candidate marked invalid by training backend")

    return (len(reasons) == 0, reasons)
