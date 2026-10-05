"""Record a maintainer decision on one citation-validated Repo Steward finding."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from descend.steward.watch import ReviewStore


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", required=True, type=Path)
    parser.add_argument("--sha", required=True)
    parser.add_argument("--finding", type=int, required=True, help="Zero-based finding index")
    parser.add_argument("--decision", choices=("confirmed", "dismissed"), required=True)
    parser.add_argument("--note", default="")
    parser.add_argument("--db", type=Path, default=Path("controller_state/steward-reviews-v2.sqlite"))
    args = parser.parse_args()
    if len(args.sha) != 40 or any(c not in "0123456789abcdef" for c in args.sha):
        parser.error("Expected full lowercase Git SHA")
    store = ReviewStore(args.db)
    try:
        result = store.decide(str(args.repo.resolve(strict=True)), args.sha, args.finding,
                              args.decision, args.note)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
