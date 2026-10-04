"""Preregistration loading and frozen parameters."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def load_preregistration(path: str | Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def default_prereg_template() -> Dict[str, Any]:
    return {
        "experiment": "DM0",
        "version": "v1-rc",
        "primary_hypothesis": "H1: T_A > T_B",
        "statistical_test": "one-sided paired randomization/permutation test on d_i = T_A,i - T_B,i",
        "delta_min": {
            "value": None,
            "status": "UNFROZEN",
            "note": "Set after pilot calibration; do not claim until frozen.",
        },
        "claim_run_n_paired_seeds": 12,
        "pilot_seeds": "separate; never reuse in claim run",
        "seed_list": {
            "status": "UNFROZEN",
            "seeds": [],
        },
        "promotion": {
            "target_improvement_margin": 0.0,
            "max_regression": 0.05,
            "require_interval_covers_delta": False,
        },
        "budgets": {
            "dev_evals_max": 5,
            "training_submissions_max": 3,
            "actions_max": 50,
            "wall_clock_budget_sec": 3600,
            "max_training_tokens": 50000,
        },
    }
