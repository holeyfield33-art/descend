"""Deterministic synthetic string-transform DSL generator."""

from __future__ import annotations

import hashlib
import json
import random
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .primitives import PRIMITIVES, PRIMITIVE_NAMES


def _seeded_rng(seed: int) -> random.Random:
    return random.Random(seed)


def _synthetic_name(rng: random.Random, index: int) -> str:
    """Generate a synthetic operator name derived from seed."""
    syllables = ["zor", "mek", "tal", "vex", "qin", "lup", "dra", "fen", "kor", "yul"]
    base = "".join(rng.choice(syllables) for _ in range(2))
    return f"{base}{index}"


@dataclass
class OperatorMapping:
    """Maps synthetic name -> underlying primitive."""
    name: str
    primitive: str
    fn: Callable[[str], str]


@dataclass
class Composition:
    """A composition of operators applied left-to-right."""
    operators: List[str]  # synthetic names
    depth: int

    def apply(self, s: str, mapping: Dict[str, OperatorMapping]) -> str:
        out = s
        for name in self.operators:
            out = mapping[name].fn(out)
        return out


@dataclass
class DSLSpec:
    seed: int
    operators: List[OperatorMapping]
    train_templates: List[Composition]  # shallow
    dev_templates: List[Composition]
    hidden_templates: List[Composition]  # deeper, never shown to agent
    regression_templates: List[Composition]
    mapping: Dict[str, OperatorMapping] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.mapping = {op.name: op for op in self.operators}


def generate_dsl(seed: int, n_ops: int = 7) -> DSLSpec:
    """
    Generate a deterministic DSL for the given seed.

    - 6–8 synthetic operator names
    - shallow (depth 1–2) train/dev compositions
    - deeper (depth 3–4) hidden transfer compositions
    - regression examples
    """
    rng = _seeded_rng(seed)
    n_ops = max(6, min(8, n_ops))
    # Deterministic choice of which primitives to expose
    chosen_prims = rng.sample(PRIMITIVE_NAMES, k=n_ops)
    operators: List[OperatorMapping] = []
    for i, prim in enumerate(chosen_prims):
        name = _synthetic_name(rng, i)
        operators.append(
            OperatorMapping(name=name, primitive=prim, fn=PRIMITIVES[prim])
        )

    names = [op.name for op in operators]

    def make_comp(depth: int) -> Composition:
        ops = [rng.choice(names) for _ in range(depth)]
        return Composition(operators=ops, depth=depth)

    # Shallow for train/dev
    train_templates = [make_comp(1) for _ in range(4)] + [make_comp(2) for _ in range(3)]
    dev_templates = [make_comp(1) for _ in range(3)] + [make_comp(2) for _ in range(2)]

    # Deeper hidden (never exposed to agent generator)
    hidden_templates = [make_comp(3) for _ in range(4)] + [make_comp(4) for _ in range(2)]

    # Regression: mix of shallow
    regression_templates = [make_comp(1) for _ in range(2)] + [make_comp(2) for _ in range(2)]

    return DSLSpec(
        seed=seed,
        operators=operators,
        train_templates=train_templates,
        dev_templates=dev_templates,
        hidden_templates=hidden_templates,
        regression_templates=regression_templates,
    )


def generate_examples(
    dsl: DSLSpec,
    templates: Sequence[Composition],
    n_per_template: int,
    example_seed: int,
    alphabet: str = "abcdefghijklmnopqrstuvwxyz0123456789",
    min_len: int = 4,
    max_len: int = 12,
) -> List[Dict[str, str]]:
    """Generate input/output pairs from templates. Deterministic given seeds."""
    rng = _seeded_rng(example_seed)
    examples: List[Dict[str, str]] = []
    for tmpl in templates:
        for _ in range(n_per_template):
            length = rng.randint(min_len, max_len)
            inp = "".join(rng.choice(alphabet) for _ in range(length))
            out = tmpl.apply(inp, dsl.mapping)
            command = json.dumps({"operators": tmpl.operators, "string": inp},
                                 sort_keys=True, separators=(",", ":"))
            examples.append({"input": command, "output": out})
    return examples
