"""Explicit controller-only .env loading; never execute shell assignments."""
from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import MutableMapping

ALLOWED_KEYS = frozenset({
    "NEBIUS_API_KEY", "AGENT_MODEL_ID", "AGENT_API_BASE",
    "TARGET_MODEL_ID", "TARGET_API_BASE", "TARGET_API_KEY",
    "REGISTRY_PATH", "WORKSPACE_ROOT",
})


class EnvironmentSyntaxError(ValueError):
    """Messages contain line numbers only, never credential values."""


def parse_environment(text: str) -> dict[str, str]:
    values: dict[str, str] = {}
    for number, line in enumerate(text.lstrip("\ufeff").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"(?:export\s+)?([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*)", line)
        if not match:
            raise EnvironmentSyntaxError(f"Invalid assignment on line {number}")
        key, value = match.groups()
        if key not in ALLOWED_KEYS or key in values:
            raise EnvironmentSyntaxError(f"Unsupported or duplicate setting on line {number}")
        if value.startswith(("'", '"')):
            quote = value[0]
            end = value.find(quote, 1)
            if end < 0 or (value[end + 1:].strip() and not value[end + 1:].strip().startswith("#")):
                raise EnvironmentSyntaxError(f"Invalid quoted value on line {number}")
            value = value[1:end]
        else:
            value = re.split(r"\s+#", value, maxsplit=1)[0].strip()
            if any(char.isspace() for char in value):
                raise EnvironmentSyntaxError(f"Quote whitespace-containing value on line {number}")
        if "\x00" in value:
            raise EnvironmentSyntaxError(f"Invalid value on line {number}")
        values[key] = value
    return values


def load_controller_environment(
    path: str | Path = ".env", *, environ: MutableMapping[str, str] | None = None,
) -> int:
    """Load into this controller process; existing environment takes precedence.

    Values are literal: no variable expansion, shell evaluation or global OS
    environment changes. Call explicitly before constructing a provider client.
    Isolated workers continue to receive the runtime's separate clean environment.
    """
    target = os.environ if environ is None else environ
    values = parse_environment(Path(path).read_text(encoding="utf-8-sig"))
    loaded = 0
    for key, value in values.items():
        if key not in target:
            target[key] = value
            loaded += 1
    return loaded


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate and load controller settings without displaying values")
    parser.add_argument("--env-file", default=".env")
    parser.add_argument("--check", action="store_true", help="Require a nonempty controller API key")
    args = parser.parse_args()
    try:
        loaded = load_controller_environment(args.env_file)
    except (EnvironmentSyntaxError, OSError, UnicodeError) as exc:
        detail = str(exc) if isinstance(exc, EnvironmentSyntaxError) else type(exc).__name__
        parser.exit(1, f"Environment check failed: {detail}\n")
    present = bool(os.environ.get("NEBIUS_API_KEY", "").strip())
    print(json.dumps({"syntax_valid": True, "settings_loaded": loaded,
                      "api_key_present": present,
                      "agent_model_configured": bool(os.environ.get("AGENT_MODEL_ID")),
                      "scope": "controller process only", "network_requests": 0}))
    if args.check and not present:
        parser.exit(1, "NEBIUS_API_KEY is missing or empty\n")


if __name__ == "__main__":
    main()
