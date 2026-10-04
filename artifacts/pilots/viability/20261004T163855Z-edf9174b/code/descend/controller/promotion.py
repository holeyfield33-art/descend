"""Config-driven promotion rule engine."""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def evaluate_promotion(
    *,
    candidate_valid: bool,
    target_delta: float,
    predicted_delta: float,
    interval_low: float,
    interval_high: float,
    regression_deltas: Dict[str, float],
    contamination_flag: bool,
    budgets_respected: bool,
    candidate_committed: bool,
    prediction_committed: bool,
    config: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Return PROMOTE or REJECT with machine-readable reasons for every criterion.

    Thresholds are config-driven; defaults are permissive for CPU harness.
    """
    cfg = config or {}
    margin = float(cfg.get("target_improvement_margin", 0.0))
    max_regression = float(cfg.get("max_regression", 0.05))
    require_interval_cover = bool(cfg.get("require_interval_covers_delta", False))

    reasons: List[Dict[str, Any]] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        reasons.append({"criterion": name, "passed": ok, "detail": detail})

    check("candidate_valid", candidate_valid)
    check("candidate_committed", candidate_committed)
    check("prediction_committed", prediction_committed)
    check("no_contamination", not contamination_flag,
          "contamination detected" if contamination_flag else "")
    check("budgets_respected", budgets_respected)

    improved = target_delta > margin
    check("target_improvement", improved,
          f"delta={target_delta}, margin={margin}")

    if require_interval_cover:
        covers = interval_low <= target_delta <= interval_high
        check("interval_covers_observed", covers,
              f"observed={target_delta}, interval=[{interval_low},{interval_high}]")
    else:
        check("interval_covers_observed", True, "not required by config")

    reg_ok = all(d >= -max_regression for d in regression_deltas.values()) if regression_deltas else True
    check("regression_tolerance", reg_ok,
          f"max_allowed_drop={max_regression}, deltas={regression_deltas}")

    all_pass = all(r["passed"] for r in reasons)
    return {
        "decision": "PROMOTE" if all_pass else "REJECT",
        "reasons": reasons,
        "target_delta": target_delta,
        "predicted_delta": predicted_delta,
    }
