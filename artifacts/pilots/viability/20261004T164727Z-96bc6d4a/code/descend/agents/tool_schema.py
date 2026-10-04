"""Small explicit tool surface shared by provider proposals and pipe dispatch."""


def _function(name, description, properties=None, required=None):
    return {"type": "function", "function": {"name": name, "description": description,
            "parameters": {"type": "object", "properties": properties or {},
                           "required": required or [], "additionalProperties": False}}}


TOOLS = [
    _function("build_dataset", "Generate a bounded training dataset. At most 100 examples total; depth 1 or 2.",
              {"n_examples": {"type": "integer", "minimum": 1, "maximum": 100},
               "max_depth": {"type": "integer", "enum": [1, 2]}}, ["n_examples", "max_depth"]),
    _function("submit_training", "Train the current candidate using this dataset; up to 3 submissions.",
              {"dataset_hash": {"type": "string"}, "config": {"type": "object",
               "properties": {"epochs": {"type": "integer", "minimum": 1, "maximum": 10},
                              "lr": {"type": "number", "minimum": 0}},
               "required": ["epochs", "lr"], "additionalProperties": False}}, ["dataset_hash", "config"]),
    _function("dev_eval", "Evaluate the current candidate on dev, consuming one capped evaluation."),
    _function("commit_candidate", "Irreversibly freeze the current candidate; optimization then closes."),
    _function("commit_prediction", "After candidate commit, irreversibly commit a quantitative prediction.",
              {"predicted_target_delta": {"type": "number"}, "interval_low": {"type": "number"},
               "interval_high": {"type": "number"},
               "predicted_regression_deltas": {"type": "object", "properties": {
                   "reg_shallow": {"type": "number"}}, "required": ["reg_shallow"], "additionalProperties": False},
               "rationale": {"type": "string"}},
              ["predicted_target_delta", "interval_low", "interval_high", "predicted_regression_deltas", "rationale"]),
    _function("read_registry", "Read a filtered view of this run's own events."),
]
ALLOWED_TOOLS = {tool["function"]["name"] for tool in TOOLS}


def tools_for_state(state):
    """Expose current operational limits; controller enforcement stays authoritative."""
    import copy
    tools = copy.deepcopy(TOOLS)
    remaining = 100 - getattr(state, "generated_examples", 0)
    candidate = getattr(state, "candidate_committed", False)
    prediction = getattr(state, "prediction_committed", False)
    available = []
    for tool in tools:
        function = tool["function"]
        name = function["name"]
        if prediction or (candidate and name not in {"commit_prediction", "read_registry"}):
            continue
        if name == "commit_prediction" and not candidate:
            continue
        if name == "build_dataset":
            if remaining <= 0:
                continue
            function["parameters"]["properties"]["n_examples"]["maximum"] = remaining
            function["description"] = f"Generate training data. {remaining} examples remain in the cumulative budget; depth 1 or 2."
        if name == "submit_training" and not state.budgets.can_train():
            continue
        if name == "dev_eval" and not state.budgets.can_dev_eval():
            continue
        available.append(tool)
    return available
