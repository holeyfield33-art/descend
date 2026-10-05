import json
from pathlib import Path

import pytest

from descend.steward.corpus import build_corpus, verify_manifest


def test_rebuild_matches_committed_frozen_corpus(tmp_path):
    result = build_corpus(tmp_path / "rebuilt")
    committed = Path(__file__).resolve().parents[1] / "eval/v1"
    assert result == {"cases": 44, "dev": 12, "test": 32,
                      "test_manifest_sha256": "e4893ad12a6d1e10863d43f5065ceaf9f0b88c2fbd565f9dd097d66d2db75043"}
    assert verify_manifest(tmp_path / "rebuilt") == verify_manifest(committed)
    assert (tmp_path / "rebuilt/manifest.json").read_bytes() == (committed / "manifest.json").read_bytes()
    with pytest.raises(ValueError, match="never overwritten"):
        build_corpus(tmp_path / "rebuilt")


def test_corpus_hash_and_path_tampering_fail_closed(tmp_path):
    build_corpus(tmp_path)
    manifest = json.loads((tmp_path / "manifest.json").read_bytes())
    manifest["cases"][0]["id"] = "../../outside"
    (tmp_path / "manifest.json").write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="identifier"):
        verify_manifest(tmp_path)


def test_corpus_execution_refuses_windows(monkeypatch, tmp_path):
    from scripts import check_steward_corpus
    monkeypatch.setattr(check_steward_corpus.sys, "platform", "win32")
    with pytest.raises(RuntimeError, match="no fallback"):
        check_steward_corpus.check_corpus(tmp_path, tmp_path / "report.json")
