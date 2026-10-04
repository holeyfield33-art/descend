"""Identical operational prompt; only model report differs between A and B."""
from descend.registry import canonical_dumps

SYSTEM_PROMPT = """You are Descend's autonomous model engineer in a PILOT, NOT CLAIM-BEARING.
Improve a separate target model on a seed-generated synthetic string-transform DSL.
Use only the offered tools and their budgets. This phase uses a fake training/scoring
backend to validate protocol operation; scores are synthetic, not evidence of learning.
Choose the dataset and training config, inspect capped dev results, and revise if useful.
Commit a final candidate, then commit your quantitative prediction and interval.
After both commits, terminate with a brief final response. Do not request hidden results.
Invoke the offered functions to act; prose or free-standing JSON does not execute a tool.
A final message closes the run. Keep responses brief until the protocol is complete.
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
    # Natural neutral prose avoids a pathological repeated-token control.
    words = ("This section contains ordinary reference prose about calendars and stationery. "
             "A page can hold several sentences. Paper may be lined or plain. "
             "A calendar displays days in sequence. Letters form words and words form sentences. "
             "A paragraph occupies part of a page. A book may contain many pages. ").split()
    neutral = "General reference material follows."
    for index in range(target + 1):
        candidate = prefix + neutral
        size = count_tokens(candidate)
        if size == target:
            return candidate
        if size > target:
            break
        next_word = words[index % len(words)]
        if count_tokens(prefix + neutral + " " + next_word) > target:
            next_word = "neutral"
        neutral += " " + next_word
    raise ValueError("Cannot match paired input length exactly with the pinned tokenizer")
