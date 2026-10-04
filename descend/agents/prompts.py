"""Identical operational prompt; only model report differs between A and B."""
from descend.registry import canonical_dumps

SYSTEM_PROMPT = """You are Descend's autonomous model engineer in a PILOT, NOT CLAIM-BEARING.
Improve a separate target model on a seed-generated synthetic string-transform DSL.
Use only the offered tools and their budgets. This phase uses a fake training/scoring
backend to validate protocol operation; scores are synthetic, not evidence of learning.
Choose the dataset and training config, inspect capped dev results, and revise if useful.
Commit a final candidate, then commit your quantitative prediction and interval.
After both commits, terminate with a brief final response. Do not request hidden results.
No code execution, raw network, credentials, controller internals or hidden data are available.
The same operational instructions apply to every arm. Work without human coaching.
"""


def user_prompt(manifest, *, reference_manifest=None, count_tokens=None):
    prefix = "Common operational information:\n" + canonical_dumps(manifest["operational"]) + "\nModel report:\n"
    if manifest["arm"] == "A":
        return prefix + canonical_dumps(manifest["target_evidence"])
    if reference_manifest is None or count_tokens is None:
        raise ValueError("Arm B requires the paired report and pinned tokenizer for length matching")
    reference = prefix + canonical_dumps(reference_manifest["target_evidence"])
    target = count_tokens(reference)
    neutral = "General reference material follows."
    for _ in range(target + 1):
        candidate = prefix + neutral
        size = count_tokens(candidate)
        if size == target:
            return candidate
        if size > target:
            break
        neutral += " neutral"
    raise ValueError("Cannot match paired input length exactly with the pinned tokenizer")
