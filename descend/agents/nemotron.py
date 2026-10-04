"""Trusted launcher; Nemotron receives JSON messages and a narrow tool schema."""
from __future__ import annotations

import json
import copy

from descend.agents.prompts import SYSTEM_PROMPT, user_prompt
from descend.agents.tool_schema import ALLOWED_TOOLS
from descend.controller.token_factory import tool_request
from descend.controller.inference import ProviderFailure
from descend.sandbox.hard_isolation import isolation_available
from descend.sandbox.transport import run_isolated_agent


def relay_source(proposals):
    """Encode untrusted arguments as data, never concatenate executable code."""
    return "PROPOSALS = " + repr(json.dumps(proposals, allow_nan=False)) + "\n" + r'''
import json, sys
responses = []
for request in json.loads(PROPOSALS):
    print(json.dumps(request), flush=True)
    responses.append(json.loads(sys.stdin.readline()))
print(json.dumps({"type": "result", "result": responses}), flush=True)
'''


class NemotronAgent:
    def __init__(self, inference, *, count_tokens, max_turns=12):
        self.inference = inference
        self.count_tokens = count_tokens
        self.max_turns = max_turns

    def run(self, manifest, controller, run_id, seed):
        if not isolation_available()["available"]:
            raise RuntimeError("Hard isolation unavailable; no provider call made")
        state = controller._require(run_id)
        messages = [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user",
                    "content": user_prompt(manifest, reference_manifest=state.reference_manifest,
                                           count_tokens=self.count_tokens)}]
        for turn in range(self.max_turns):
            try:
                evidence = self.inference.complete(messages, state, seed=seed)
                state.transcript.append({"provider_inference": copy.deepcopy(evidence)})
                controller.registry.append("provider_inference", run_id, state.arm, state.seed,
                    {k: evidence[k] for k in ("reservation_id", "provider_tokens",
                                             "accounted_upper_bound_usd", "estimated_list_price_usd")})
                message = evidence["response"]["choices"][0]["message"]
                assistant = {"role": "assistant", "content": message.get("content")}
                calls = message.get("tool_calls") or []
                if calls:
                    assistant["tool_calls"] = calls
                messages.append(assistant)
                if not calls:
                    if state.candidate_committed and state.prediction_committed:
                        return {"status": "completed", "turns": turn + 1}
                    controller._fail(run_id, "agent terminated before commitments")
                    return {"status": "incomplete", "turns": turn + 1}
                if len(calls) > 8:
                    raise ValueError("Too many tool calls in one response")
                proposals = [tool_request(call, allowed_tools=ALLOWED_TOOLS) for call in calls]
                responses = run_isolated_agent(controller, run_id, relay_source(proposals))
                for call, response in zip(calls, responses, strict=True):
                    messages.append({"role": "tool", "tool_call_id": call["id"],
                                     "content": json.dumps(response, allow_nan=False)})
            except Exception as exc:
                category = "infrastructure" if isinstance(exc, ProviderFailure) else "agent"
                controller._fail(run_id, f"Nemotron loop failed: {type(exc).__name__}", category=category)
                return {"status": "failed", "category": category, "error_type": type(exc).__name__,
                        "turns": turn + 1}
        controller._fail(run_id, "agent turn cap exhausted")
        return {"status": "failed", "error_type": "TurnCap", "turns": self.max_turns}
