"""Offline Descend diagnostics."""
import argparse
import json
from pathlib import Path

from descend.steward.doctor import diagnose


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["doctor"])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--require-act", action="store_true")
    args = parser.parse_args()
    report = diagnose(args.root)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report["act_ready" if args.require_act else "protocol_ready"] else 1)


if __name__ == "__main__":
    main()
