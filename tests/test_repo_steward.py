import subprocess

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
