"""Deterministic grading of string-transform predictions."""

from __future__ import annotations

from typing import Dict, List, Sequence


def grade(
    predictions: Sequence[Dict[str, str]],
    gold: Sequence[Dict[str, str]],
) -> Dict[str, float]:
    """
    Exact-match accuracy.

    predictions and gold are lists of {"input": ..., "output": ...}.
    Matching is by input string; missing predictions count as incorrect.
    """
    def unique_map(items):
        result = {}
        for item in items:
            key, value = item.get("input", ""), item.get("output", "")
            if key in result and result[key] != value:
                raise ValueError("Conflicting outputs for the same task input")
            result[key] = value
        return result

    gold_map = unique_map(gold)
    if not gold_map:
        return {"accuracy": 0.0, "n": 0, "correct": 0}

    correct = 0
    for inp, pred in unique_map(predictions).items():
        if inp in gold_map and pred == gold_map[inp]:
            correct += 1

    n = len(gold_map)
    return {
        "accuracy": correct / n if n else 0.0,
        "n": float(n),
        "correct": float(correct),
    }


def grade_regression(
    predictions: Dict[str, Sequence[Dict[str, str]]],
    gold: Dict[str, Sequence[Dict[str, str]]],
) -> Dict[str, Dict[str, float]]:
    """Grade multiple named regression sets."""
    return {name: grade(predictions.get(name, []), g) for name, g in gold.items()}
