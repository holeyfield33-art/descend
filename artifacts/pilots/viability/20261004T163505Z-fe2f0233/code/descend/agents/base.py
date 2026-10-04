"""Base agent interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class BaseAgent(ABC):
    @abstractmethod
    def run(self, manifest: Dict[str, Any], controller_api: Any) -> Dict[str, Any]:
        """Execute the adaptation loop; return transcript summary."""
        ...
