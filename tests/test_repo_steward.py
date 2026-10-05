import subprocess
import threading

import pytest

from descend.steward.watch import ReviewStore, commit_snapshot, scan_once


def _git(path, *args):
    subprocess.run(["git", "-C", str(path), *args], check=True, capture_output=True)


def test_once_persists_review_and_deduplicates(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "add app")
    store = ReviewStore(tmp_path / "state.sqlite")
    calls = []

    def reviewer(snapshot):
        calls.append(snapshot["sha"])
        return {"content": "reviewed"}

    first = scan_once(repo, store, reviewer)
    second = scan_once(repo, ReviewStore(tmp_path / "state.sqlite"), reviewer)
    assert first["status"] == "reviewed"
    assert first["review"]["content"] == "reviewed"
    assert second["cached"] is True
    assert len(calls) == 1


def test_sensitive_content_never_reaches_reviewer(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "app.py").write_text('api_key = "abcdefgh12345678"\n', encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "add app")
    assert commit_snapshot(repo)["status"] == "skipped_sensitive_content"
    result = scan_once(repo, ReviewStore(tmp_path / "state.sqlite"),
                       lambda _: (_ for _ in ()).throw(AssertionError("provider called")))
    assert result["status"] == "skipped_sensitive_content"


def test_atomic_claim_prevents_second_paid_attempt(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "add app")
    store = ReviewStore(tmp_path / "state.sqlite")
    entered, release = threading.Event(), threading.Event()
    calls = []

    def reviewer(snapshot):
        calls.append(snapshot["sha"])
        entered.set()
        assert release.wait(5)
        return {"content": "done"}

    thread = threading.Thread(target=lambda: scan_once(repo, store, reviewer))
    thread.start()
    try:
        assert entered.wait(5)
        second = scan_once(repo, ReviewStore(tmp_path / "state.sqlite"), reviewer)
        assert second["cached"] is True
        assert second["status"] == "in_progress"
        assert len(calls) == 1
    finally:
        release.set()
        thread.join(5)
    assert store.recent()[0]["status"] == "reviewed"


def test_failed_review_is_not_retried_automatically(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init")
    _git(repo, "config", "user.name", "Test")
    _git(repo, "config", "user.email", "test@example.invalid")
    (repo / "app.py").write_text("x = 1\n", encoding="utf-8")
    _git(repo, "add", "app.py")
    _git(repo, "commit", "-m", "add app")
    store = ReviewStore(tmp_path / "state.sqlite")
    with pytest.raises(RuntimeError):
        scan_once(repo, store, lambda _: (_ for _ in ()).throw(RuntimeError("provider failed")))
    result = scan_once(repo, store, lambda _: (_ for _ in ()).throw(AssertionError("retried")))
    assert result["status"] == "error"
    assert result["cached"] is True


def test_maintainer_decision_persists_and_requires_validated_finding(tmp_path):
    store = ReviewStore(tmp_path / "state.sqlite")
    snapshot = {"repo": "test-repo", "sha": "a" * 40, "status": "ready", "diff": ""}
    assert store.claim(snapshot)
    row = {"repo": "test-repo", "sha": "a" * 40, "status": "reviewed",
           "review": {"findings": [{"path": "app.py", "line": 1, "evidence": "x = 1"}]}}
    store.update(row)
    stored = store.decide("test-repo", "a" * 40, 0, "confirmed", "Reproduced locally")
    assert stored["decision"] == "confirmed"
    assert ReviewStore(tmp_path / "state.sqlite").recent()[0]["decisions"][0]["note"] == "Reproduced locally"
    with pytest.raises(ValueError):
        store.decide("test-repo", "a" * 40, 1, "dismissed")
