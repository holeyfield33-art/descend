"""Agent-writable workspace (Zone 1) with path jail."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .isolation import assert_path_inside


class Workspace:
    def __init__(self, root: str | Path, run_id: str):
        self.root = (Path(root) / run_id).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        for sub in ("scratch", "datasets", "configs", "notes"):
            (self.root / sub).mkdir(exist_ok=True)

    def path(self, relative: str) -> Path:
        if not relative or relative.startswith("/") or relative.startswith("\\"):
            raise PermissionError("absolute paths not allowed in workspace")
        parts = Path(relative).parts
        if ".." in parts:
            raise PermissionError("path traversal (..) not allowed")
        return assert_path_inside(self.root, relative)

    def write(self, relative: str, content: str) -> None:
        p = self.path(relative)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")

    def read(self, relative: str) -> str:
        return self.path(relative).read_text(encoding="utf-8")

    def write_bytes(self, relative: str, data: bytes) -> None:
        p = self.path(relative)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def read_bytes(self, relative: str) -> bytes:
        return self.path(relative).read_bytes()
