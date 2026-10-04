"""Trusted launcher for a fake worker executing in the OS sandbox."""
import json
from descend.sandbox.transport import run_isolated_agent


class FakeAgent:
    def __init__(self, behavior="success"):
        if behavior not in ("success", "fail_train", "no_commit"):
            raise ValueError("unknown behavior")
        self.behavior = behavior

    def run(self, manifest, controller, run_id, seed):
        # Compatibility signature used only on the host launcher.
        # The controller object and seed never cross the worker pipes.
        return run_isolated_agent(controller, run_id, fake_worker_source(manifest, self.behavior))


def fake_worker_source(manifest, behavior):
    return "MANIFEST = " + repr(json.dumps(manifest)) + "\nBEHAVIOR = " + repr(behavior) + "\n" + r'''
import json, sys
manifest = json.loads(MANIFEST)
def call(tool, args):
    print(json.dumps({"tool": tool, "args": args}), flush=True)
    response = json.loads(sys.stdin.readline())
    if not response["ok"]:
        raise RuntimeError("tool rejected")
    return response["result"]
dataset = call("build_dataset", {"n_examples": 16, "max_depth": 2})
status = "abandoned"
if BEHAVIOR != "no_commit":
    trained = call("submit_training", {"dataset_hash": dataset["dataset_hash"],
        "config": {"epochs": 1, "lr": 0.0001, "force_fail": BEHAVIOR == "fail_train"}})
    status = "train_failed"
    if trained["status"] == "success":
        call("commit_candidate", {})
        prediction = {"predicted_target_delta": 0.15, "interval_low": 0.05,
            "interval_high": 0.30, "predicted_regression_deltas": {"reg_shallow": -0.01},
            "rationale": "Fake worker predicts modest improvement."}
        call("commit_prediction", prediction)
        status = "completed"
print(json.dumps({"type": "result", "result": {"status": status}}), flush=True)
'''
