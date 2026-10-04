"""Budgeted controller-side adaptation of the cookbook's OpenAI chat example."""
from __future__ import annotations

import json
import time

from descend.controller.token_factory import INFERENCE_BASE_URL, chat_request
from descend.controller.budgets import BudgetExhausted

# Verified official Nano prices: $0.06 input / $0.24 output per million.
# Reserve/settle at $1 per million for BOTH, above those rates. This is a
# conservative accounting bound, not a provider billing receipt.
NANO_MODEL_ID = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
SUPER_MODEL_ID = "nvidia/nemotron-3-super-120b-a12b"
SUPPORTED_MODELS = {NANO_MODEL_ID, SUPER_MODEL_ID}
PRICE_POLICY = {NANO_MODEL_ID: (1, 0.06, 0.24), SUPER_MODEL_ID: (2, 0.30, 0.90)}


class ProviderFailure(RuntimeError):
    pass


class TokenFactoryInference:
    def __init__(self, *, api_key, ledger, model=NANO_MODEL_ID, client=None):
        if model not in SUPPORTED_MODELS:
            raise ValueError("Model has no verified inference price policy")
        self.ledger = ledger
        self.model = model
        if client is None:
            from openai import OpenAI
            import httpx
            client = OpenAI(api_key=api_key, base_url=INFERENCE_BASE_URL,
                            max_retries=0, timeout=60,
                            http_client=httpx.Client(trust_env=False, follow_redirects=False))
        self.client = client

    def complete(self, messages, state, *, seed, max_tokens=4096):
        from descend.agents.tool_schema import tools_for_state
        if type(max_tokens) is not int or not 1 <= max_tokens <= 8192:
            raise ValueError("Invalid completion cap")
        state.budgets.check()
        tools = tools_for_state(state)
        body = chat_request(model=self.model, messages=messages, max_tokens=max_tokens, tools=tools or None)
        body.update(temperature=0, seed=seed)
        body["tool_choice"] = "none" if (getattr(state, "candidate_committed", False)
            and getattr(state, "prediction_committed", False)) else "auto"
        # NVIDIA's documented vLLM/OpenAI request pattern for reasoning off.
        # Validate provider behavior in pilots; keep the exact setting in evidence.
        body["extra_body"] = {"chat_template_kwargs": {"enable_thinking": False}}
        # UTF-8 byte count bounds text tokens for the pinned byte-level tokenizer;
        # allowance covers provider/tool chat wrapping.
        input_bound = len(json.dumps(body, ensure_ascii=False).encode("utf-8")) + 8192
        if input_bound > 120_000:
            raise BudgetExhausted("Inference input cap exhausted")
        if state.budgets.tokens_used + input_bound + max_tokens > state.budgets.agent_token_budget:
            state.budgets.breached = True
            raise BudgetExhausted("Inference token reservation exceeds run budget")
        rate_bound, input_price, output_price = PRICE_POLICY[self.model]
        reservation = self.ledger.reserve(state.run_id, (input_bound + max_tokens) * rate_bound)
        deadline = state.budgets.wall_clock_budget_sec - (time.monotonic() - state.budgets.started_at)
        try:
            response = self.client.chat.completions.create(**body, timeout=min(60, max(0.1, deadline)))
        except Exception as exc:
            raise ProviderFailure(f"Provider call failed: {type(exc).__name__}; reservation retained") from None
        record = response.model_dump(mode="json")
        usage = record.get("usage") or {}
        prompt, completion = usage.get("prompt_tokens"), usage.get("completion_tokens")
        if any(type(n) is not int or n < 0 for n in (prompt, completion)):
            raise ProviderFailure("Provider omitted valid token usage; reservation retained")
        total = prompt + completion
        if prompt > input_bound or completion > max_tokens:
            self.ledger.settle(reservation, max(input_bound + max_tokens + 1, total) * rate_bound, record.get("id", ""))
            raise ProviderFailure("Provider exceeded token reservation")
        self.ledger.settle(reservation, total * rate_bound, record.get("id", ""))
        state.budgets.record_tokens(total)
        return {"request": body, "response": record, "reservation_id": reservation,
                "provider_tokens": total, "accounted_upper_bound_usd": total * rate_bound / 1_000_000,
                "estimated_list_price_usd": (prompt * input_price + completion * output_price) / 1_000_000}
