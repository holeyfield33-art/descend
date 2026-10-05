"""Generate a new owned corpus directory without executing fixture code."""
import argparse
import json
from pathlib import Path

from descend.steward.corpus import build_corpus


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(build_corpus(args.output), indent=2))


if __name__ == "__main__":
    main()
