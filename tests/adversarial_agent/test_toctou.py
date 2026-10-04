"""TOCTOU: post-commit mutation of artifacts must be detected."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

import pytest
from descend.sandbox.hard_isolation import isolation_available

pytestmark = pytest.mark.skipif(not isolation_available()["available"],
                               reason="isolated fake worker requires Linux namespace privileges")

from descend.controller import Controller, BudgetState
from descend.registry import RegistryStore
from descend.agents.fake_agent import FakeAgent


def test_mutate_frozen_candidate_detected_before_hidden_eval():
    with tempfile.TemporaryDirectory() as tmp:
        ctl = Controller(
            registry=RegistryStore(Path(tmp) / "reg"),
            workspace_root=Path(tmp) / "runs",
            controller_root=Path(tmp) / "ctrl",
        )
        agent = FakeAgent()
        start = ctl.start_run("A", seed=300, budgets=BudgetState())
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 300)

        state = ctl._runs[run_id]
        frozen_path = Path(state.candidate["_frozen_path"])
        assert frozen_path.is_file()

        # Adversary mutates the frozen file after commit
        data = json.loads(frozen_path.read_text())
        data["adapter_hash"] = "0" * 64
        frozen_path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

        with pytest.raises(RuntimeError, match="TOCTOU"):
            ctl.hidden_eval(run_id)


def test_mutate_frozen_prediction_detected():
    with tempfile.TemporaryDirectory() as tmp:
        ctl = Controller(
            registry=RegistryStore(Path(tmp) / "reg"),
            workspace_root=Path(tmp) / "runs",
            controller_root=Path(tmp) / "ctrl",
        )
        agent = FakeAgent()
        start = ctl.start_run("A", seed=301, budgets=BudgetState())
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 301)

        state = ctl._runs[run_id]
        pred_path = Path(state.prediction["_frozen_path"])
        data = json.loads(pred_path.read_text())
        data["predicted_target_delta"] = 999.0
        pred_path.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

        with pytest.raises(RuntimeError, match="TOCTOU"):
            ctl.hidden_eval(run_id)


def test_in_memory_mutation_does_not_affect_frozen_eval():
    """Mutating state.candidate in memory after freeze should not change frozen file."""
    with tempfile.TemporaryDirectory() as tmp:
        ctl = Controller(
            registry=RegistryStore(Path(tmp) / "reg"),
            workspace_root=Path(tmp) / "runs",
            controller_root=Path(tmp) / "ctrl",
        )
        agent = FakeAgent()
        start = ctl.start_run("A", seed=302, budgets=BudgetState())
        run_id = start["run_id"]
        agent.run(start["manifest"], ctl, run_id, 302)
        state = ctl._runs[run_id]
        original_hash = state.candidate["adapter_hash"]
        state.candidate["adapter_hash"] = "evil" * 16
        # Frozen file still has original; verify passes on frozen content
        # (in-memory evil value is not what _verify checks for adapter on file)
        # _verify compares frozen file hash to _frozen_hash and adapter_hash on file
        # vs state — state.adapter_hash was mutated so this SHOULD raise
        with pytest.raises(RuntimeError, match="TOCTOU"):
            ctl.hidden_eval(run_id)
        # restore and succeed
        state.candidate["adapter_hash"] = original_hash
        result = ctl.hidden_eval(run_id)
        assert "target_delta" in result
