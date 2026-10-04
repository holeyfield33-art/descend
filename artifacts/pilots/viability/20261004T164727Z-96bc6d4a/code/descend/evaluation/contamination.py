"""Contamination checker: agent training data vs hidden data."""

from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any, Dict, List, Sequence


def _normalize(s: str) -> str:
    return " ".join(s.lower().split())


def _sha(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def _ngrams(s: str, n: int = 3) -> Counter:
    tokens = s.split()
    if len(tokens) < n:
        return Counter([" ".join(tokens)] if tokens else [])
    return Counter(" ".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1))


def check_contamination(
    training: Sequence[Dict[str, str]],
    hidden: Sequence[Dict[str, str]],
    ngram_n: int = 3,
    ngram_threshold: float = 0.5,
) -> Dict[str, Any]:
    """
    Compare agent-created training data against hidden examples.

    Checks:
      - exact normalized match on input or output
      - SHA-256 exact-content overlap
      - configurable n-gram overlap
    """
    flags: List[str] = []
    exact_matches = 0
    sha_matches = 0

    hidden_inputs = {_normalize(h["input"]) for h in hidden}
    hidden_outputs = {_normalize(h["output"]) for h in hidden}
    hidden_shas = {_sha(h["input"] + "||" + h["output"]) for h in hidden}
    hidden_ng = Counter()
    for h in hidden:
        hidden_ng.update(_ngrams(_normalize(h["input"] + " " + h["output"]), ngram_n))

    train_ng = Counter()
    for t in training:
        ni = _normalize(t.get("input", ""))
        no = _normalize(t.get("output", ""))
        if ni in hidden_inputs or no in hidden_outputs:
            exact_matches += 1
            flags.append("exact_normalized")
        content_sha = _sha(t.get("input", "") + "||" + t.get("output", ""))
        if content_sha in hidden_shas:
            sha_matches += 1
            flags.append("sha256_exact")
        train_ng.update(_ngrams(ni + " " + no, ngram_n))

    # Simple Jaccard-like on ngram keys
    if train_ng and hidden_ng:
        inter = sum((train_ng & hidden_ng).values())
        union = sum((train_ng | hidden_ng).values())
        ngram_sim = inter / union if union else 0.0
    else:
        ngram_sim = 0.0

    if ngram_sim >= ngram_threshold:
        flags.append(f"ngram_overlap:{ngram_sim:.3f}")

    contaminated = bool(flags)
    return {
        "contaminated": contaminated,
        "exact_matches": exact_matches,
        "sha_matches": sha_matches,
        "ngram_similarity": ngram_sim,
        "flags": list(set(flags)),
    }
