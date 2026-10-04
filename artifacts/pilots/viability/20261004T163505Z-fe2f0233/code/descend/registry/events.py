"""Registry event types and helpers for DM0."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional
from uuid import uuid4

from .hashchain import GENESIS_HASH, compute_event_hash


# Minimum event types required by the directive
EVENT_TYPES = frozenset({
    "run_start",
    "manifest_issued",
    "provider_inference",
    "dataset_created",
    "dev_eval",
    "training_submitted",
    "training_completed",
    "candidate_created",
    "candidate_committed",
    "prediction_committed",
    "hidden_eval",
    "decision",
    "run_failure",
    "run_end",
})


def make_event(
    event_type: str,
    run_id: str,
    arm: str,
    seed: int,
    payload: Dict[str, Any],
    previous_hash: str = GENESIS_HASH,
    event_id: Optional[str] = None,
    timestamp: Optional[str] = None,
) -> Dict[str, Any]:
    """Construct a fully hashed registry event."""
    if event_type not in EVENT_TYPES:
        raise ValueError(f"Unknown event type: {event_type}")

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()
    if event_id is None:
        event_id = str(uuid4())

    body = {
        "event_id": event_id,
        "event_type": event_type,
        "timestamp": timestamp,
        "run_id": run_id,
        "arm": arm,
        "seed": seed,
        "payload": payload,
    }
    event_hash = compute_event_hash(body, previous_hash)
    return {
        **body,
        "previous_hash": previous_hash,
        "event_hash": event_hash,
    }
