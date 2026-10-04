"""Agent cannot access hidden examples, seeds, evaluator, promotion, or registry history mutation."""

from __future__ import annotations

import tempfile

from descend.controller import Controller, BudgetState
from descend.registry import RegistryStore


def test_manifest_has_no_hidden_examples():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        start = ctl.start_run("A", seed=11, budgets=BudgetState())
        manifest = start["manifest"]
        blob = str(manifest)
        # Must not contain actual hidden template definitions or example pairs
        assert "hidden_templates" not in blob
        # Operational text may mention the restriction phrase; that is fine
        assert "splits" not in manifest
        assert "hidden" not in start  # top-level start payload


def test_agent_cannot_read_hidden_via_start():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        start = ctl.start_run("A", seed=22)
        assert "splits" not in start
        assert "hidden" not in start


def test_registry_append_only_from_controller():
    with tempfile.TemporaryDirectory() as tmp:
        reg = RegistryStore(tmp)
        ctl = Controller(registry=reg)
        start = ctl.start_run("A", seed=33)
        run_id = start["run_id"]
        view = reg.read_only_view(run_id)
        assert isinstance(view, list)
        assert not hasattr(reg, "rewrite")
        assert not hasattr(reg, "delete_event")
