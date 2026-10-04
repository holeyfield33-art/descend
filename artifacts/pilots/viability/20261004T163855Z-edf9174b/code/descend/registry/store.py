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
        ok, error = self.verify(run_id)
        if not ok:
            raise RuntimeError(f"Cannot append to invalid registry: {error}")
        previous_events = self.events(run_id)
        prev = previous_events[-1]["event_hash"] if previous_events else GENESIS_HASH
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
            f.flush()
            os.fsync(f.fileno())
        # Independent controller-owned head detects a valid-prefix truncation.
        # Crash between log/anchor writes fails closed rather than silently adopting.
        anchor_path = path.with_suffix(".anchor.json")
        temporary = anchor_path.with_suffix(".tmp")
        with temporary.open("w", encoding="utf-8") as f:
            f.write(canonical_dumps({"event_count": len(previous_events) + 1,
                                     "head_hash": event["event_hash"]}))
            f.flush()
            os.fsync(f.fileno())
        os.replace(temporary, anchor_path)
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
        try:
            events = self.events(run_id)
            valid, error = verify_chain(events)
            if not valid:
                return valid, error
            anchor_path = self._path(run_id).with_suffix(".anchor.json")
            if not anchor_path.exists():
                return (False, "missing head anchor (legacy/unanchored log)") if events else (True, None)
            anchor = json.loads(anchor_path.read_text(encoding="utf-8"))
            if anchor != {"event_count": len(events),
                          "head_hash": events[-1]["event_hash"] if events else GENESIS_HASH}:
                return False, "head anchor mismatch (truncation or crash)"
            return True, None
        except (ValueError, KeyError, OSError, TypeError) as exc:
            return False, f"registry unreadable: {type(exc).__name__}"

    def read_only_view(self, run_id: str, arm: Optional[str] = None) -> List[Dict[str, Any]]:
        evs = self.events(run_id)
        if arm is not None:
            evs = [e for e in evs if e.get("arm") == arm]
        allowed = {"run_start": ("arm", "budgets"),
                   "manifest_issued": ("arm", "manifest_hash"),
                   "dataset_created": ("dataset_hash", "n_examples", "source", "contamination"),
                   "training_submitted": ("dataset_hash", "config"),
                   "training_completed": ("status", "adapter_id", "adapter_hash"),
                   "dev_eval": ("dev_accuracy",),
                   "candidate_committed": ("identity",),
                   "prediction_committed": ("prediction_hash",)}
        return [{"event_type": e["event_type"],
                 "payload": {k: e["payload"][k] for k in allowed[e["event_type"]]
                             if k in e["payload"]}}
                for e in evs if e["event_type"] in allowed]
