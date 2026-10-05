"""Show locally stored Repo Steward reviews in a loopback-only browser page."""
import argparse
from pathlib import Path

from descend.steward.dashboard import serve_dashboard
from descend.steward.watch import ReviewStore


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, default=Path("controller_state/steward-reviews-v2.sqlite"))
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    serve_dashboard(ReviewStore(args.db), args.port)


if __name__ == "__main__":
    main()
