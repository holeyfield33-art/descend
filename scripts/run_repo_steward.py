"""Poll one explicitly selected Git checkout for new commits and review them read-only."""
from __future__ import annotations

import argparse
import json
import os
import time
from pathlib import Path

from descend.controller.environment import load_controller_environment
from descend.controller.spend import SpendLedger
from descend.steward.reviewer import review_with_nemotron
from descend.steward.watch import ReviewStore, scan_once


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, help="Explicit Git checkout root to watch")
    parser.add_argument("--once", action="store_true", help="Scan once; default is persistent polling")
    parser.add_argument("--interval", type=int, default=60, help="Polling seconds, at least 10")
    parser.add_argument("--live", action="store_true", help="Use paid Nemotron review; otherwise record mock output")
    parser.add_argument("--env-file", default=".env", help="Controller-only environment file")
    args = parser.parse_args()
    if args.interval < 10:
        parser.error("Interval must be at least 10 seconds")
    # Mock observations must never suppress a later real review of the same commit.
    store_name = "steward-reviews-v2.sqlite" if args.live else "steward-mock-v2.sqlite"
    store = ReviewStore(Path("controller_state") / store_name)
    if args.live:
        load_controller_environment(args.env_file)
        key = os.environ.get("NEBIUS_API_KEY", "").strip()
        if not key:
            parser.error("NEBIUS_API_KEY missing")
        ledger = SpendLedger(Path("controller_state") / "cloud-spend.sqlite")
        reviewer = lambda snapshot: review_with_nemotron(snapshot, api_key=key, ledger=ledger)
    else:
        reviewer = lambda snapshot: {"model": None, "content": "MOCK ONLY: no model review performed",
                                     "accounted_upper_bound_usd": 0, "formal_data": False}
    while True:
        try:
            result = scan_once(args.repo, store, reviewer)
        except Exception as exc:
            # The failed commit is sealed in SQLite and will not trigger another
            # automatic provider call. Keep watching for a future commit.
            result = {"status": "error", "error_type": type(exc).__name__}
        print(json.dumps(result, ensure_ascii=False), flush=True)
        if args.once:
            break
        time.sleep(args.interval)


if __name__ == "__main__":
    main()
