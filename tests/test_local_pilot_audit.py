from pathlib import Path

import pytest

from scripts import audit_local_pilot


def test_real_adapter_pilot_verifies_and_false_score_is_rejected(monkeypatch):
    root = Path(__file__).resolve().parents[1] / "artifacts/pilots/local-training/20261004T171319Z"
    assert audit_local_pilot.audit(root)["training_tokens"] == 690
    original = audit_local_pilot.read
    def altered(path):
        value = original(path)
        if Path(path).name == "adapted_dev.json":
            value["score"]["accuracy"] = 1
        return value
    monkeypatch.setattr(audit_local_pilot, "read", altered)
    with pytest.raises(AssertionError):
        audit_local_pilot.audit(root)
