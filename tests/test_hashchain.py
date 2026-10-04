"""Tamper detection on hash chains."""

from __future__ import annotations

import copy
import tempfile

from descend.registry import RegistryStore, verify_chain, detect_tampering


def _make_chain(tmp: str, n: int = 4):
    store = RegistryStore(tmp)
    for i in range(n):
        store.append("run_start" if i == 0 else "dev_eval", "r1", "A", 1, {"i": i})
    return store.events("r1")


def test_valid_chain():
    with tempfile.TemporaryDirectory() as tmp:
        events = _make_chain(tmp)
        ok, err = verify_chain(events)
        assert ok, err


def test_altered_payload_fails():
    with tempfile.TemporaryDirectory() as tmp:
        events = _make_chain(tmp)
        bad = copy.deepcopy(events)
        bad[1]["payload"]["i"] = 999
        ok, err = verify_chain(bad)
        assert not ok
        assert "hash mismatch" in (err or "")


def test_deleted_event_fails():
    with tempfile.TemporaryDirectory() as tmp:
        events = _make_chain(tmp)
        bad = events[:2] + events[3:]  # drop index 2
        ok, err = verify_chain(bad)
        assert not ok


def test_reordered_fails():
    with tempfile.TemporaryDirectory() as tmp:
        events = _make_chain(tmp)
        bad = [events[0], events[2], events[1], events[3]]
        ok, err = verify_chain(bad)
        assert not ok


def test_detect_tampering():
    with tempfile.TemporaryDirectory() as tmp:
        orig = _make_chain(tmp)
        bad = copy.deepcopy(orig)
        bad[1]["payload"]["i"] = -1
        issues = detect_tampering(orig, bad)
        assert any("altered" in i or "invalid" in i for i in issues)
