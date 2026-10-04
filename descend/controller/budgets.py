"""Budget counters and enforcement."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict
from time import monotonic


@dataclass
class BudgetState:
    dev_evals_used: int = 0
    dev_evals_max: int = 5
    training_submissions_used: int = 0
    training_submissions_max: int = 3
    actions_used: int = 0
    actions_max: int = 50
    wall_clock_budget_sec: int = 3600
    agent_token_budget: int = 100_000
    max_training_tokens: int = 50_000
    tokens_used: int = 0
    training_tokens_used: int = 0
    breached: bool = False
    started_at: float = field(default_factory=monotonic, repr=False)

    def check(self) -> None:
        if self.breached or monotonic() - self.started_at > self.wall_clock_budget_sec:
            self.breached = True
            raise BudgetExhausted("run budget exhausted")

    def respected(self) -> bool:
        return (not self.breached and self.actions_used <= self.actions_max
                and self.tokens_used <= self.agent_token_budget
                and self.training_tokens_used <= self.max_training_tokens
                and self.training_submissions_used <= self.training_submissions_max
                and self.dev_evals_used <= self.dev_evals_max
                and monotonic() - self.started_at <= self.wall_clock_budget_sec)

    def record_tokens(self, count: int, *, training: bool = False) -> None:
        self.check()
        if count < 0:
            raise ValueError("negative token count")
        attr = "training_tokens_used" if training else "tokens_used"
        cap = self.max_training_tokens if training else self.agent_token_budget
        if getattr(self, attr) + count > cap:
            self.breached = True
            raise BudgetExhausted("token budget exhausted")
        setattr(self, attr, getattr(self, attr) + count)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "dev_evals_used": self.dev_evals_used,
            "dev_evals_max": self.dev_evals_max,
            "training_submissions_used": self.training_submissions_used,
            "training_submissions_max": self.training_submissions_max,
            "actions_used": self.actions_used,
            "actions_max": self.actions_max,
            "wall_clock_budget_sec": self.wall_clock_budget_sec,
            "agent_token_budget": self.agent_token_budget,
            "max_training_tokens": self.max_training_tokens,
            "tokens_used": self.tokens_used,
            "training_tokens_used": self.training_tokens_used,
            "breached": self.breached,
        }

    def can_dev_eval(self) -> bool:
        return self.dev_evals_used < self.dev_evals_max

    def can_train(self) -> bool:
        return self.training_submissions_used < self.training_submissions_max

    def can_act(self) -> bool:
        return self.actions_used < self.actions_max

    def record_dev_eval(self) -> None:
        if not self.can_dev_eval():
            self.breached = True
            raise BudgetExhausted("dev_evaluation budget exhausted")
        self.record_action()
        self.dev_evals_used += 1

    def record_training(self) -> None:
        if not self.can_train():
            self.breached = True
            raise BudgetExhausted("training_submission budget exhausted")
        self.record_action()
        self.training_submissions_used += 1

    def record_action(self) -> None:
        self.check()
        if not self.can_act():
            self.breached = True
            raise BudgetExhausted("action budget exhausted")
        self.actions_used += 1


class BudgetExhausted(Exception):
    pass
