"""Primary statistics for DM0: one-sided paired randomization test."""

from __future__ import annotations

import itertools
import math
from typing import Any, Dict, List, Optional, Sequence, Tuple


def paired_differences(t_a: Sequence[float], t_b: Sequence[float]) -> List[float]:
    if len(t_a) != len(t_b):
        raise ValueError("t_a and t_b must have equal length")
    return [a - b for a, b in zip(t_a, t_b)]


def one_sided_sign_flip_pvalue(
    diffs: Sequence[float],
    n_perms: Optional[int] = None,
) -> float:
    """
    Exact (or approximate) one-sided paired randomization / sign-flip test.

    H1: mean(d) > 0  (T_A > T_B)
    Under the null, signs of d_i are exchangeable.
    p = proportion of sign-flip means >= observed mean.
    """
    diffs = list(diffs)
    n = len(diffs)
    if n == 0:
        return 1.0
    observed = sum(diffs) / n

    if n_perms is None or n_perms >= 2 ** n:
        # Exact enumeration
        count = 0
        total = 0
        for signs in itertools.product([-1, 1], repeat=n):
            m = sum(s * d for s, d in zip(signs, diffs)) / n
            if m >= observed - 1e-15:
                count += 1
            total += 1
        return count / total

    # Monte-Carlo approximation
    import random
    rng = random.Random(0)
    count = 0
    for _ in range(n_perms):
        flipped = [d if rng.random() < 0.5 else -d for d in diffs]
        m = sum(flipped) / n
        if m >= observed - 1e-15:
            count += 1
    return count / n_perms


def summarize_pairs(
    t_a: Sequence[float],
    t_b: Sequence[float],
    delta_min: Optional[float] = None,
    n_perms: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Full primary-result summary.

    Reports individual diffs, mean, median, wins, failures, p-value,
    and whether practical effect threshold passed (if delta_min set).
    """
    diffs = paired_differences(t_a, t_b)
    n = len(diffs)
    mean_d = sum(diffs) / n if n else 0.0
    sorted_d = sorted(diffs)
    median_d = (
        sorted_d[n // 2]
        if n % 2 == 1
        else (sorted_d[n // 2 - 1] + sorted_d[n // 2]) / 2
        if n
        else 0.0
    )
    a_wins = sum(1 for d in diffs if d > 0)
    b_wins = sum(1 for d in diffs if d < 0)
    ties = sum(1 for d in diffs if d == 0)

    p = one_sided_sign_flip_pvalue(diffs, n_perms=n_perms)

    practical = None
    if delta_min is not None:
        practical = mean_d >= delta_min

    return {
        "n": n,
        "differences": diffs,
        "mean_difference": mean_d,
        "median_difference": median_d,
        "a_wins": a_wins,
        "b_wins": b_wins,
        "ties": ties,
        "one_sided_pvalue": p,
        "delta_min": delta_min,
        "practical_effect_passed": practical,
        "hypothesis": "H1: T_A > T_B (one-sided)",
    }
