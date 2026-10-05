import json

import pytest

from descend.steward.fleet import load_fleet


def test_explicit_multi_repo_config_and_separate_modes(tmp_path):
    first, second = tmp_path / "one", tmp_path / "two"
    first.mkdir()
    second.mkdir()
    config = tmp_path / "fleet.json"
    config.write_text(json.dumps({"repositories": [
        {"path": "one", "mode": "mock", "interval_seconds": 10},
        {"path": "two", "mode": "live", "interval_seconds": 60}]}), encoding="utf-8")
    rows = load_fleet(config)
    assert [row["path"] for row in rows] == [first, second]
    assert [row["mode"] for row in rows] == ["mock", "live"]


def test_duplicate_or_unpaired_context_is_rejected(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    report = tmp_path / "report.json"
    report.write_text("{}", encoding="utf-8")
    config = tmp_path / "fleet.json"
    config.write_text(json.dumps({"repositories": [{"path": "repo"}, {"path": "repo"}]}),
                      encoding="utf-8")
    with pytest.raises(ValueError, match="duplicated"):
        load_fleet(config)
    config.write_text(json.dumps({"repositories": [{"path": "repo", "mode": "live",
                                                    "vibe_report": "report.json"}]}), encoding="utf-8")
    with pytest.raises(ValueError, match="paired"):
        load_fleet(config)
