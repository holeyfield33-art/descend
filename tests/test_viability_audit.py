from pathlib import Path

import pytest

from scripts import audit_viability


def test_saved_pilot_verifies_and_adapter_tampering_is_rejected(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "artifacts/pilots/viability/20261004T164240Z-2e8cb6fd"
    assert audit_viability.audit(root)["completed"] == 2
    original = audit_viability.byte_hash
    monkeypatch.setattr(audit_viability, "byte_hash",
                        lambda path: "tampered" if Path(path).name == "adapter.bin" else original(path))
    with pytest.raises(AssertionError):
        audit_viability.audit(root)
