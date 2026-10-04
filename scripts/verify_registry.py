#!/usr/bin/env python3
"""Verify a registry chain for a given run_id."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from descend.registry import RegistryStore


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("run_id")
    parser.add_argument("--registry", default="./registry_data")
    args = parser.parse_args()

    store = RegistryStore(args.registry)
    ok, err = store.verify(args.run_id)
    if ok:
        print(f"OK: chain for {args.run_id} is valid ({len(store.events(args.run_id))} events)")
    else:
        print(f"FAIL: {err}")
        sys.exit(1)


if __name__ == "__main__":
    main()
