"""Canonical JSON serialization for hashing.

Uses sorted keys, no whitespace variation, consistent number/string handling.
"""

from __future__ import annotations

import json
from typing import Any


def canonical_dumps(obj: Any) -> str:
    """Serialize to a deterministic JSON string suitable for hashing."""
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        default=_default,
    )


def _default(obj: Any) -> Any:
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if isinstance(obj, bytes):
        return obj.hex()
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def canonical_hash(obj: Any) -> str:
    """SHA-256 of canonical JSON of obj."""
    import hashlib

    data = canonical_dumps(obj).encode("utf-8")
    return hashlib.sha256(data).hexdigest()
