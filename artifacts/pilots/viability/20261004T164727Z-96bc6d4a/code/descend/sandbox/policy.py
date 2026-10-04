"""Sandbox policy — no credentials, no unrestricted network."""

from __future__ import annotations

FORBIDDEN_PATTERNS = [
    "NEBIUS",
    "HUGGINGFACE",
    "HF_TOKEN",
    "API_KEY",
    "SECRET",
]


def check_scratch_content(text: str) -> list[str]:
    """Return list of policy violations found in agent scratch text."""
    violations = []
    upper = text.upper()
    for pat in FORBIDDEN_PATTERNS:
        if pat in upper:
            violations.append(f"forbidden pattern: {pat}")
    return violations
