"""Candidate identity changes when any bound component changes."""

from __future__ import annotations

from descend.candidate import build_candidate_identity, compute_component_hash


def test_identity_changes_with_each_component():
    base = {
        "base_hash": "a" * 64,
        "adapter_hash": "b" * 64,
        "training_dataset_hash": "c" * 64,
        "training_config_hash": "d" * 64,
        "agent_transcript_hash": "e" * 64,
        "evaluator_code_hash": "f" * 64,
        "controller_code_hash": "g" * 64,
        "promotion_rule_hash": "h" * 64,
    }
    id0 = build_candidate_identity(**base)["identity_hash"]

    for key in base:
        mutated = dict(base)
        mutated[key] = "z" * 64
        id1 = build_candidate_identity(**mutated)["identity_hash"]
        assert id1 != id0, f"Changing {key} should change identity"


def test_stable_for_same_inputs():
    kwargs = {
        "base_hash": "1" * 64,
        "adapter_hash": "2" * 64,
        "training_dataset_hash": "3" * 64,
        "training_config_hash": "4" * 64,
        "agent_transcript_hash": "5" * 64,
        "evaluator_code_hash": "6" * 64,
        "controller_code_hash": "7" * 64,
        "promotion_rule_hash": "8" * 64,
    }
    a = build_candidate_identity(**kwargs)["identity_hash"]
    b = build_candidate_identity(**kwargs)["identity_hash"]
    assert a == b
