"""Hash-chained append-only event log primitives."""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List, Optional, Tuple

from .canonical import canonical_dumps, canonical_hash


GENESIS_HASH = "0" * 64


def compute_event_hash(payload: Dict[str, Any], previous_hash: str) -> str:
    """Hash of previous_hash + canonical payload."""
    material = {
        "previous_hash": previous_hash,
        "payload": payload,
    }
    return canonical_hash(material)


def verify_chain(events: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Verify an ordered list of events.

    Each event must contain:
      - event_hash
      - previous_hash
      - and the rest of the payload fields used for hashing.

    Returns (ok, error_message).
    """
    if not events:
        return True, None

    expected_prev = GENESIS_HASH
    for i, ev in enumerate(events):
        if "event_hash" not in ev:
            return False, f"Event {i} missing event_hash"
        if "previous_hash" not in ev:
            return False, f"Event {i} missing previous_hash"

        prev = ev["previous_hash"]
        if prev != expected_prev:
            return False, f"Event {i} previous_hash mismatch: expected {expected_prev}, got {prev}"

        # Reconstruct payload without the two hash fields
        payload = {k: v for k, v in ev.items() if k not in ("event_hash", "previous_hash")}
        computed = compute_event_hash(payload, prev)
        if computed != ev["event_hash"]:
            return False, f"Event {i} hash mismatch: expected {computed}, got {ev['event_hash']}"

        expected_prev = ev["event_hash"]

    return True, None


def detect_tampering(original: List[Dict[str, Any]], candidate: List[Dict[str, Any]]) -> List[str]:
    """Return list of detected anomalies between two chains."""
    issues: List[str] = []
    ok_o, err_o = verify_chain(original)
    ok_c, err_c = verify_chain(candidate)
    if not ok_o:
        issues.append(f"original chain invalid: {err_o}")
    if not ok_c:
        issues.append(f"candidate chain invalid: {err_c}")

    if len(candidate) < len(original):
        issues.append(f"deleted events: original length {len(original)}, candidate {len(candidate)}")
    if len(candidate) > len(original):
        # append is normal; only flag if early divergence
        pass

    min_len = min(len(original), len(candidate))
    for i in range(min_len):
        if original[i].get("event_hash") != candidate[i].get("event_hash"):
            issues.append(f"event {i} altered or reordered")
            break
    return issues
