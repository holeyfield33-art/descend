"""Append-only registry store with hash chain verification."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .canonical import canonical_dumps
from .events import make_event
from .hashchain import GENESIS_HASH, verify_chain


class RegistryStore:
    """File-backed append-only event log, one file per run_id."""

    def __init__(self, root: str | Path = "./registry_data"):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, run_id: str) -> Path:
        safe = run_id.replace("/", "_").replace("\\", "_")
        return self.root / f"{safe}.jsonl"

    def append(
        self,
        event_type: str,
        run_id: str,
        arm: str,
        seed: int,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        prev = self.last_hash(run_id)
        event = make_event(
            event_type=event_type,
            run_id=run_id,
            arm=arm,
            seed=seed,
            payload=payload,
            previous_hash=prev,
        )
        path = self._path(run_id)
        with path.open("a", encoding="utf-8") as f:
            f.write(canonical_dumps(event) + "\n")
        return event

    def events(self, run_id: str) -> List[Dict[str, Any]]:
        path = self._path(run_id)
        if not path.exists():
            return []
        out: List[Dict[str, Any]] = []
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    out.append(json.loads(line))
        return out

    def last_hash(self, run_id: str) -> str:
        evs = self.events(run_id)
        if not evs:
            return GENESIS_HASH
        return evs[-1]["event_hash"]

    def verify(self, run_id: str) -> tuple[bool, Optional[str]]:
        return verify_chain(self.events(run_id))

    def read_only_view(self, run_id: str, arm: Optional[str] = None) -> List[Dict[str, Any]]:
        evs = self.events(run_id)
        if arm is not None:
            evs = [e for e in evs if e.get("arm") == arm]
        return evs
