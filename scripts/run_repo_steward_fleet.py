"""Poll an explicit allowlist of Git repositories, with per-repo mock/live modes."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from descend.controller.environment import load_controller_environment
from descend.controller.spend import SpendLedger
from descend.steward.fleet import load_fleet
from descend.steward.reviewer import review_with_nemotron
from descend.steward.vibe_context import load_vibe_context
from descend.steward.watch import ReviewStore, scan_once


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--env-file", default=".env")
    args = parser.parse_args()
    try:
        fleet = load_fleet(args.config)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    live = any(item["mode"] == "live" for item in fleet)
    key, ledger = None, None
    if live:
        load_controller_environment(args.env_file)
        key = os.environ.get("NEBIUS_API_KEY", "").strip()
        if not key:
            parser.error("NEBIUS_API_KEY missing for live repository")
        ledger = SpendLedger(Path("controller_state") / "cloud-spend.sqlite")
    # Share the single-repo command's durable stores and dashboard.
    stores = {"mock": ReviewStore(Path("controller_state") / "steward-mock-v2.sqlite"),
              "live": ReviewStore(Path("controller_state") / "steward-reviews-v2.sqlite")}
    due = {str(item["path"]): 0.0 for item in fleet}
    while True:
        for item in fleet:
            repo = str(item["path"])
            if not args.once and time.monotonic() < due[repo]:
                continue
            due[repo] = time.monotonic() + item["interval_seconds"]
            def reviewer(snapshot):
                if item["mode"] == "mock":
                    return {"model": None, "content": "MOCK ONLY: no model review performed",
                            "accounted_upper_bound_usd": 0, "formal_data": False}
                context = (load_vibe_context(item["vibe_report"], item["asi_catalog"], commit=snapshot["sha"])
                           if item["vibe_report"] else None)
                return review_with_nemotron(snapshot, api_key=key, ledger=ledger, static_context=context)
            try:
                result = scan_once(repo, stores[item["mode"]], reviewer)
                output = {"repo": repo, "mode": item["mode"], "result": result}
            except Exception as exc:
                output = {"repo": repo, "mode": item["mode"], "status": "error",
                          "error_type": type(exc).__name__}
            print(json.dumps(output, ensure_ascii=False), flush=True)
        if args.once:
            break
        time.sleep(1)


if __name__ == "__main__":
    main()
