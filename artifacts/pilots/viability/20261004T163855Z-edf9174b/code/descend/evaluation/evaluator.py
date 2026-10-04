"""Hidden evaluator — controller-only."""

from __future__ import annotations

from typing import Any, Dict, Sequence

from descend.dsl.grader import grade


def evaluate_hidden(
    predictions: Sequence[Dict[str, str]],
    hidden_gold: Sequence[Dict[str, str]],
) -> Dict[str, Any]:
    """Exact-match grading on hidden set. One-shot only."""
    return grade(predictions, hidden_gold)
