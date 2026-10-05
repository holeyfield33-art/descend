import importlib.metadata
import sys

from descend.steward import doctor


def test_doctor_records_drift_and_never_claims_act_ready(tmp_path, monkeypatch):
    (tmp_path / ".python-version").write_text("3.14.4\n")
    (tmp_path / ".python-version.windows").write_text("3.14.6\n")
    (tmp_path / "requirements-lock.txt").write_text("pytest==9.1.1\nmissing-fixture==1\n")
    def version(name):
        if name == "pytest":
            return "9.1.1"
        raise importlib.metadata.PackageNotFoundError(name)
    monkeypatch.setattr(doctor.importlib.metadata, "version", version)
    monkeypatch.setattr(doctor, "isolation_available", lambda: {"available": True})
    result = doctor.diagnose(tmp_path)
    assert result["dependency_mismatches"] == [{"package": "missing-fixture", "expected": "1", "actual": None}]
    assert not result["protocol_ready"]
    assert not result["act_ready"]
    assert result["provider_calls"] == 0
    assert len(result["lock_sha256"]) == 64
    assert result["python_pin"] == ("3.14.6" if sys.platform == "win32" else "3.14.4")
