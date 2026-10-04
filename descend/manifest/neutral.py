"""Arm B length-matched neutral content."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .build import default_operational


def _pad_to_length(text: str, target_len: int, pad_char: str = "·") -> str:
    if len(text) >= target_len:
        return text[:target_len]
    return text + (pad_char * (target_len - len(text)))


def build_arm_b_neutral(
    *,
    arm_a_manifest: Dict[str, Any],
    budgets: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Arm B = common operating information + neutral length-matched text
    in place of target-specific evidence.
    """
    ops = default_operational(budgets)
    # Approximate length of the target_evidence block for matching
    import json
    evidence_str = json.dumps(arm_a_manifest.get("target_evidence", {}), sort_keys=True)
    neutral_body = (
        "This control arm receives identical operational information and budgets. "
        "No target-model architecture, checkpoint, parameter, tokenizer, baseline, "
        "or lineage evidence is supplied. Neutral filler follows to approximate "
        "payload length for the control comparison."
    )
    neutral_text = _pad_to_length(neutral_body, max(len(evidence_str), 200))
    return {
        "arm": "B",
        "operational": ops,
        "neutral_content": neutral_text,
        "neutral_content_length": len(neutral_text),
    }
