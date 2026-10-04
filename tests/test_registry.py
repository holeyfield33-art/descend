"""Registry store and event basics."""

from __future__ import annotations

import tempfile
from pathlib import Path

from descend.registry import RegistryStore, verify_chain, GENESIS_HASH


def test_append_and_verify():
    with tempfile.TemporaryDirectory() as tmp:
        store = RegistryStore(tmp)
        e1 = store.append("run_start", "r1", "A", 1, {"x": 1})
        assert e1["previous_hash"] == GENESIS_HASH
        e2 = store.append("manifest_issued", "r1", "A", 1, {"y": 2})
        assert e2["previous_hash"] == e1["event_hash"]
        ok, err = store.verify("r1")
        assert ok, err
        assert len(store.events("r1")) == 2


def test_empty_chain():
    with tempfile.TemporaryDirectory() as tmp:
        store = RegistryStore(tmp)
        ok, err = store.verify("nonexistent")
        assert ok
