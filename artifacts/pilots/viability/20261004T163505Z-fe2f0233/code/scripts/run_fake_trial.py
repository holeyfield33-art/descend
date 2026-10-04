#!/usr/bin/env python3
"""Run a single CPU-only fake-agent trial end-to-end."""

from __future__ import annotations

import json
import sys
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from descend.controller import Controller, BudgetState
from descend.registry import RegistryStore
from descend.agents.fake_agent import FakeAgent


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Descend DM0 fake trial")
    parser.add_argument("--arm", choices=["A", "B", "C"], default="A")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--registry", default="./registry_data")
    parser.add_argument("--behavior", default="success", choices=["success", "fail_train", "no_commit"])
    args = parser.parse_args()

    registry = RegistryStore(args.registry)
    controller = Controller(registry=registry)
    budgets = BudgetState()

    start = controller.start_run(arm=args.arm, seed=args.seed, budgets=budgets)
    run_id = start["run_id"]
    print(f"Started run: {run_id}")
    print(f"Manifest arm: {start['manifest'].get('arm')}")

    if args.arm == "C":
        from descend.baselines.scripted_lora import run_scripted_lora
        result = run_scripted_lora(controller, run_id, args.seed)
    else:
        agent = FakeAgent(behavior=args.behavior)
        result = agent.run(start["manifest"], controller, run_id, args.seed)

    print(f"Agent status: {result.get('status')}")

    if result.get("status") == "completed":
        hidden = controller.hidden_eval(run_id)
        print(f"Hidden eval: {json.dumps(hidden, indent=2)}")
        decision = controller.decide(run_id)
        print(f"Decision: {decision['decision']}")
        print(json.dumps(decision, indent=2))
    else:
        # Still close the run with zero-gain semantics
        decision = controller.decide(run_id)
        print(f"Decision (failure path): {decision['decision']}")

    ok, err = registry.verify(run_id)
    print(f"Registry chain valid: {ok}" + (f" ({err})" if err else ""))

    # Dump events
    events = registry.events(run_id)
    print(f"\n--- Registry events ({len(events)}) ---")
    for e in events:
        print(f"  {e['event_type']}: {e['event_hash'][:12]}...")


if __name__ == "__main__":
    main()
