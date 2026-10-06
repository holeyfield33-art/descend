import json
import subprocess
from pathlib import Path

import pytest

from descend.sandbox.hard_isolation import isolation_available
from descend.steward.act import ActStore, ProposalRejected, validate_proposal, verify_proposal

FINDING = {"path": "app.py", "line": 2, "evidence": "return sum(values[:-1])", "reason": "seeded off-by-one", "severity": "low", "verification": "run reproducer"}
DIFF = "--- a/app.py\n+++ b/app.py\n@@ -1,2 +1,2 @@\n def solve(values):\n-    return sum(values)\n+    return sum(values[:-1])\n"
TEST = "from app import solve\n\ndef test_reproducer():\n    assert solve([1, 2, 3]) == 6\n"
FIX = "def solve(values):\n    return sum(values)\n"
BUG = "def solve(values):\n    return sum(values[:-1])\n"


def proposal(test=TEST, replacement=FIX):
    return json.dumps(dict(path="app.py", test_source=test, replacement_source=replacement, expected_failure="AssertionError"))


def fixture(tmp_path):
    source = tmp_path / "source"
    (source / "tests").mkdir(parents=True)
    (source / "app.py").write_text(BUG)
    (source / "tests/test_existing.py").write_text("from app import solve\n\ndef test_public_api():\n    assert callable(solve)\n")
    return source


def test_action_claim_zero_cap_replay_and_commit_cap(tmp_path):
    store = ActStore(tmp_path / "acts.sqlite")
    assert not store.claim("owned", "a"*40, 0, commit_cap=0)
    assert store.claim("owned", "a"*40, 0)
    assert not store.claim("owned", "a"*40, 0, commit_cap=2)
    assert not store.claim("owned", "a"*40, 1)
    assert ActStore(tmp_path / "acts.sqlite").claim("owned", "b"*40, 0)


@pytest.mark.parametrize("change", [
    {"path": "../app.py"}, {"path": "tests/test_existing.py"},
    {"approval": "approved"}, {"expected_failure": []},
    {"test_source": "import os\ndef test_reproducer():\n    assert False\n"},
    {"test_source": "from app import solve\ndef test_reproducer():\n    return\n    assert False\n"},
    {"replacement_source": "def solve(values):\n    return solve.__globals__\n"},
])
def test_untrusted_schema_and_code_rejected(change):
    data = json.loads(proposal())
    data.update(change)
    with pytest.raises(ProposalRejected):
        validate_proposal(json.dumps(data), FINDING)


def test_windows_act_refuses_without_running_code(tmp_path, monkeypatch):
    from descend.steward import act_worker
    monkeypatch.setattr(act_worker, "isolation_available", lambda: {"available": False})
    evidence = verify_proposal(fixture(tmp_path), FINDING, proposal(), tmp_path / "export", review_diff=DIFF)
    assert evidence["classification"] == "ERROR"
    assert evidence["patch_export"] is None


def test_tampered_target_is_classified_without_execution(tmp_path):
    raw = json.loads(proposal())
    raw["path"] = "tests/test_reproducer.py"
    evidence = verify_proposal(fixture(tmp_path), FINDING, json.dumps(raw), tmp_path / "export", review_diff=DIFF)
    assert evidence["classification"] == "TAMPERED"
    assert "existing_before" not in evidence
    assert evidence["patch_export"] is None


def test_git_materialization_uses_reviewed_blobs_without_checkout(tmp_path):
    from scripts.run_steward_act import materialize_git
    repo = fixture(tmp_path)
    def git(*args):
        return subprocess.run(["git", "-c", "core.hooksPath=" + __import__('os').devnull,
                               "-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
                               "-C", str(repo), *args], check=True, capture_output=True).stdout
    git("init")
    git("add", ".")
    git("commit", "-m", "owned fixture")
    sha = git("rev-parse", "HEAD").decode().strip()
    destination = tmp_path / "detached"
    destination.mkdir()
    diff = materialize_git(repo, sha, destination)
    assert (destination / "app.py").read_text() == BUG
    assert not (destination / ".git").exists()
    assert '+    return sum(values[:-1])' in diff
    assert git("status", "--porcelain") == b""


@pytest.mark.skipif(not isolation_available()["available"], reason="Act execution requires Linux namespaces")
@pytest.mark.parametrize("raw, expected", [
    (proposal(), "PATCH_VERIFIED"),
    (proposal(replacement=None), "REPRODUCED"),
    (proposal(replacement=BUG), "PATCH_FAILED"),
    (proposal(test="from app import solve\ndef test_reproducer():\n    assert solve([1,2,3]) == 3\n"), "NOT_REPRODUCED"),
])
def test_offline_classification_and_original_test_hash(tmp_path, raw, expected):
    source = fixture(tmp_path)
    evidence = verify_proposal(source, FINDING, raw, tmp_path / "export", review_diff=DIFF)
    assert evidence["classification"] == expected, evidence
    assert evidence["source_root_unchanged"] is True
    assert (source / "app.py").read_text() == BUG
    if expected == "PATCH_VERIFIED":
        assert evidence["patch_export"].endswith(".patch")
        assert len(evidence["test_sha256"]) == 64
