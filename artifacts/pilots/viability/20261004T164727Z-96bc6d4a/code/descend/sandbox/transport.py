"""Controller-owned dispatch for one run; workers receive only JSON pipes."""
import copy
import json
import time
from descend.tools.build_dataset import build_dataset_from_policy
from .hard_isolation import run_in_hard_isolation


class ToolSession:
    def __init__(self, controller, run_id):
        self.controller = controller
        self.run_id = run_id
        self.generated = 0

    def dispatch(self, request):
        state = self.controller._require(self.run_id)
        before = state.budgets.actions_used
        try:
            return self._dispatch(request)
        finally:
            if state.budgets.actions_used == before:
                state.budgets.record_action()

    def _dispatch(self, request):
        if set(request) != {"tool", "args"} or not isinstance(request["args"], dict):
            raise ValueError("invalid envelope")
        tool, args = request["tool"], request["args"]
        state = self.controller._require(self.run_id)
        state.budgets.record_tokens(len(json.dumps(request)))
        if tool == "build_dataset":
            if set(args) != {"n_examples", "max_depth"}:
                raise ValueError("invalid arguments")
            n, depth = args["n_examples"], args["max_depth"]
            if type(n) is not int or type(depth) is not int or not 1 <= n <= 100 or depth not in (1, 2):
                state.budgets.breached = True
                raise ValueError("generation policy")
            if self.generated + n > 100:
                state.budgets.breached = True
                raise ValueError("generation budget")
            examples = build_dataset_from_policy(state.dsl_seed, n, depth)[:n]
            self.generated += len(examples)
            result = self.controller.create_dataset(self.run_id, examples)
        elif tool == "submit_training":
            if set(args) != {"dataset_hash", "config"}:
                raise ValueError("invalid arguments")
            result = self.controller.submit_training(self.run_id, **args)
        elif tool == "commit_candidate":
            if args:
                raise ValueError("invalid arguments")
            result = self.controller.commit_candidate(self.run_id)
        elif tool == "commit_prediction":
            result = self.controller.commit_prediction(self.run_id, args)
        elif tool == "dev_examples":
            if args:
                raise ValueError("invalid arguments")
            result = self.controller.get_dev_examples(self.run_id)
        elif tool == "dev_eval":
            if args:
                raise ValueError("invalid arguments")
            result = self.controller.dev_eval(self.run_id)
        elif tool == "read_registry":
            if args:
                raise ValueError("invalid arguments")
            result = self.controller.read_registry(self.run_id)
        else:
            raise ValueError("tool not allowed")
        state.transcript.append(copy.deepcopy({"request": request, "response": result}))
        state.budgets.record_tokens(len(json.dumps(result)))
        return result


def run_isolated_agent(controller, run_id, source):
    state = controller._require(run_id)
    state.budgets.check()
    state.budgets.record_tokens(len(source.encode("utf-8")))
    session = ToolSession(controller, run_id)
    result = run_in_hard_isolation(
        source, workspace=controller.workspace_root / run_id / "workspace",
        controller_root=controller.roots.base,
        timeout_sec=min(30, max(0, state.budgets.wall_clock_budget_sec -
                                  (time.monotonic() - state.budgets.started_at))),
        tool_handler=session.dispatch,
    )
    if not result["ok"]:
        if result.get("timed_out"):
            state.budgets.breached = True
        category = "agent" if result.get("isolation", {}).get("available") else "infrastructure"
        controller._fail(run_id, "isolated agent failed", category=category)
        raise RuntimeError("isolated agent unavailable or failed; no soft fallback")
    state.budgets.record_tokens(len(json.dumps(result["result"])))
    return result["result"]
