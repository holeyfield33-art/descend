"""Train / dev / hidden split generation with strict isolation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .generator import DSLSpec, generate_examples


@dataclass
class DataSplits:
    seed: int
    train: List[Dict[str, str]]
    dev: List[Dict[str, str]]
    hidden: List[Dict[str, str]]
    regression: List[Dict[str, str]]
    # Metadata only controller sees
    train_template_depths: List[int]
    hidden_template_depths: List[int]


def make_splits(
    dsl: DSLSpec,
    train_n_per: int = 8,
    dev_n_per: int = 4,
    hidden_n_per: int = 6,
    regression_n_per: int = 4,
    split_seed: int | None = None,
    hidden_seed: int | None = None,
) -> DataSplits:
    """
    Create isolated splits.

    Hidden examples use only hidden_templates (deeper compositions).
    Agent-facing generators must never receive hidden_templates.
    """
    base = split_seed if split_seed is not None else dsl.seed
    train = generate_examples(dsl, dsl.train_templates, train_n_per, example_seed=base + 1)
    dev = generate_examples(dsl, dsl.dev_templates, dev_n_per, example_seed=base + 2)
    hidden = generate_examples(dsl, dsl.hidden_templates, hidden_n_per,
                               example_seed=hidden_seed if hidden_seed is not None else base + 3)
    regression = generate_examples(
        dsl, dsl.regression_templates, regression_n_per, example_seed=base + 4
    )
    return DataSplits(
        seed=base,
        train=train,
        dev=dev,
        hidden=hidden,
        regression=regression,
        train_template_depths=[t.depth for t in dsl.train_templates],
        hidden_template_depths=[t.depth for t in dsl.hidden_templates],
    )
