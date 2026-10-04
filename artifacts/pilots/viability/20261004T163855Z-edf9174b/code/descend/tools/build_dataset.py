"""Tool: build_dataset — agent requests examples from permitted classes only."""

from __future__ import annotations

from typing import Any, Dict, List

from descend.dsl import generate_dsl, generate_examples


def build_dataset_from_policy(
    seed: int,
    n_examples: int,
    max_depth: int = 2,
) -> List[Dict[str, str]]:
    """
    Generate training examples using only shallow templates.
    Controller must enforce that hidden depths are never requested.
    """
    dsl = generate_dsl(seed)
    # Only use train templates (depths 1–2)
    allowed = [t for t in dsl.train_templates if t.depth <= max_depth]
    if not allowed:
        allowed = dsl.train_templates[:1]
    n_per = max(1, n_examples // max(len(allowed), 1))
    return generate_examples(dsl, allowed, n_per, example_seed=seed + 99)
