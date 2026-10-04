from types import SimpleNamespace

from descend.agents.tool_schema import TOOLS, tools_for_state
from descend.controller import BudgetState


def test_tool_surface_tracks_exhaustion_and_commit_order():
    state = SimpleNamespace(budgets=BudgetState(), generated_examples=60,
                            candidate_committed=False, prediction_committed=False)
    by_name = lambda: {t["function"]["name"]: t["function"] for t in tools_for_state(state)}
    assert by_name()["build_dataset"]["parameters"]["properties"]["n_examples"]["maximum"] == 40
    assert "commit_prediction" not in by_name()
    state.generated_examples = 100
    state.budgets.training_submissions_used = state.budgets.training_submissions_max
    state.budgets.dev_evals_used = state.budgets.dev_evals_max
    assert set(by_name()) == {"commit_candidate", "read_registry"}
    state.candidate_committed = True
    assert set(by_name()) == {"commit_prediction", "read_registry"}
    state.prediction_committed = True
    assert tools_for_state(state) == []
    assert TOOLS[0]["function"]["parameters"]["properties"]["n_examples"]["maximum"] == 100
