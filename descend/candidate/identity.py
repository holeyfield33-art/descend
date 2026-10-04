"""Candidate / run identity binding via SHA-256 of canonical components."""

from __future__ import annotations

from typing import Any, Dict, Optional

from descend.registry.canonical import canonical_hash


def compute_component_hash(obj: Any) -> str:
    return canonical_hash(obj)


def build_candidate_identity(
    *,
    base_hash: str,
    adapter_hash: str,
    training_dataset_hash: str,
    training_config_hash: str,
    agent_transcript_hash: str,
    evaluator_code_hash: str,
    controller_code_hash: str,
    promotion_rule_hash: str,
    extra: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """
    Build the full candidate/run identity document.

    Required bindings (Correction 4):
      H(base), H(adapter), H(training dataset), H(training config),
      H(agent transcript), H(evaluator code), H(controller code), H(promotion rule)
    """
    components = {
        "H_base": base_hash,
        "H_adapter": adapter_hash,
        "H_training_dataset": training_dataset_hash,
        "H_training_config": training_config_hash,
        "H_agent_transcript": agent_transcript_hash,
        "H_evaluator_code": evaluator_code_hash,
        "H_controller_code": controller_code_hash,
        "H_promotion_rule": promotion_rule_hash,
    }
    if extra:
        components.update(extra)

    identity_hash = canonical_hash(components)
    return {
        "components": components,
        "identity_hash": identity_hash,
    }


# Placeholder hashes for CPU-only phase (deterministic stubs)
STUB_EVALUATOR_HASH = canonical_hash({"module": "descend.evaluation.evaluator", "version": "0.1.0"})
STUB_CONTROLLER_HASH = canonical_hash({"module": "descend.controller.controller", "version": "0.1.0"})
STUB_PROMOTION_HASH = canonical_hash({"module": "descend.controller.promotion", "version": "0.1.0"})
STUB_BASE_HASH = canonical_hash({"model": "stub-base", "version": "cpu-fake"})
