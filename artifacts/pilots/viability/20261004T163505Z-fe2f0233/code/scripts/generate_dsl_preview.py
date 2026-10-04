#!/usr/bin/env python3
"""Preview a generated DSL for a seed."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from descend.dsl import generate_dsl, make_splits


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    dsl = generate_dsl(args.seed)
    splits = make_splits(dsl, split_seed=args.seed)

    print(f"Seed: {args.seed}")
    print("Operators:")
    for op in dsl.operators:
        print(f"  {op.name} -> {op.primitive}")
    print(f"Train templates depths: {[t.depth for t in dsl.train_templates]}")
    print(f"Hidden templates depths: {[t.depth for t in dsl.hidden_templates]}")
    print(f"Train examples: {len(splits.train)}")
    print(f"Dev examples: {len(splits.dev)}")
    print(f"Hidden examples: {len(splits.hidden)}")
    print("Sample train:")
    for ex in splits.train[:3]:
        print(f"  {ex['input']!r} -> {ex['output']!r}")


if __name__ == "__main__":
    main()
