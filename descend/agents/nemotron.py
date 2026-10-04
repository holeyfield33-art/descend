"""Nemotron agent placeholder — not wired in CPU phase."""

from __future__ import annotations

from typing import Any, Dict

from .base import BaseAgent


class NemotronAgent(BaseAgent):
    def run(self, manifest: Dict[str, Any], controller_api: Any) -> Dict[str, Any]:
        raise NotImplementedError(
            "Nemotron agent is not implemented in the CPU-only phase. "
            "Use FakeAgent for harness validation."
        )
