"""Read-only verification of preserved pilot evidence; never evaluates H1."""
import argparse
import json
from pathlib import Path

from descend.controller.provenance import byte_hash
from descend.registry import RegistryStore, canonical_hash


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def audit(root):
    if not __debug__:
        raise RuntimeError("Evidence audit requires Python assertions enabled; omit -O")
    root = Path(root)
    plan, results, gate = (read(root / name) for name in ("plan.json", "results.json", "gate.json"))
    assert plan["formal_data"] is False and plan["training_backend"] == "fake"
    attempts = results["results"]
    assert len(attempts) == len(plan["attempts"]) == gate["attempts"] == 4
    assert [{"arm": r["arm"], "seed": r["seed"]} for r in attempts] == plan["attempts"]
    assert gate["completed"] == sum(r["status"] == "completed" for r in attempts)
    assert gate["go"] == (gate["completed"] >= 3)
    snapshot = root / "source_snapshot.json"
    if snapshot.exists():
        files = read(snapshot)
        assert canonical_hash(files) == plan["runtime"]["source_snapshot_hash"]
        assert all(byte_hash(root / "code" / name) == digest for name, digest in files.items())
    provider_calls, estimated_usd, accounted_usd = 0, 0.0, 0.0
    for result in attempts:
        directory = root / result["run_id"]
        store = RegistryStore(directory)
        assert store.verify(result["run_id"])[0]
        events = store.events(result["run_id"])
        verification = read(directory / "registry_verification.json")
        assert verification["valid"] and verification["event_count"] == len(events)
        assert byte_hash(directory / (result["run_id"] + ".jsonl")) == verification["log_hash"]
        assert byte_hash(directory / (result["run_id"] + ".anchor.json")) == verification["anchor_hash"]
        transcript = read(directory / "transcript.json")
        assert canonical_hash(transcript) == result["transcript_hash"]
        manifest = read(directory / "manifest.json")
        assert canonical_hash(manifest["manifest"]) == manifest["manifest_hash"]
        assert manifest["input_content_tokens"] == manifest["paired_a_content_tokens"]
        inference_events = [e for e in events if e["event_type"] == "provider_inference"]
        evidence = [entry["provider_inference"] for entry in transcript if "provider_inference" in entry]
        assert len(inference_events) == len(evidence)
        for event, call in zip(inference_events, evidence, strict=True):
            assert event["payload"]["reservation_id"] == call["reservation_id"]
            assert call["request"]["model"] == plan["agent_model"]
            assert call["response"]["model"] == plan["agent_model"]
            usage = call["response"]["usage"]
            assert usage["prompt_tokens"] + usage["completion_tokens"] == call["provider_tokens"]
            estimated_usd += call["estimated_list_price_usd"]
            accounted_usd += call["accounted_upper_bound_usd"]
            provider_calls += 1
        types = [e["event_type"] for e in events]
        if result["status"] == "completed":
            assert types.count("hidden_eval") == 1
            assert types.index("candidate_committed") < types.index("prediction_committed") < types.index("hidden_eval")
            assert read(directory / "hidden_result.json")["synthetic"]
            candidate = read(directory / "committed/candidate.json")
            identity = candidate["identity"]
            components = identity["components"]
            assert canonical_hash(components) == identity["identity_hash"]
            assert components["H_base"] == canonical_hash({"model": "stub-base", "version": "cpu-fake"})
            assert components["H_controller_code"] == plan["runtime"]["controller_code_hash"]
            assert components["H_evaluator_code"] == plan["runtime"]["evaluator_code_hash"]
            if snapshot.exists():
                assert components["H_controller_code"] == canonical_hash(
                    {name: digest for name, digest in files.items() if name.startswith("descend/")})
                assert components["H_evaluator_code"] == canonical_hash(
                    {name: digest for name, digest in files.items() if name.startswith(("descend/evaluation/", "descend/dsl/"))
                     or name == "descend/controller/controller.py"})
                assert components["H_promotion_rule"] == canonical_hash({"source_hash": canonical_hash(
                    {"descend/controller/promotion.py": files["descend/controller/promotion.py"]}), "configuration": {}})
            for name, filename in (("H_adapter", "adapter.bin"), ("H_training_dataset", "dataset.json"),
                                   ("H_training_config", "training-config.json")):
                assert byte_hash(directory / "committed" / filename) == components[name]
            assert any(canonical_hash(transcript[:n]) == components["H_agent_transcript"]
                       for n in range(len(transcript) + 1))
            prediction = read(directory / "committed/prediction.json")
            committed = next(e for e in events if e["event_type"] == "prediction_committed")
            assert canonical_hash(prediction) == committed["payload"]["prediction_hash"]
            assert read(directory / "decision.json")["predicted_delta"] == prediction["predicted_target_delta"]
        else:
            assert "hidden_eval" not in types
    return {"batch": root.name, "verified": True, "attempts": 4,
            "completed": gate["completed"], "go": gate["go"],
            "source_snapshot_available": snapshot.exists(), "provider_calls": provider_calls,
            "estimated_list_price_usd": estimated_usd, "accounted_upper_bound_usd": accounted_usd,
            "formal_data": False, "training_backend": "fake"}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="artifacts/pilots/viability")
    args = parser.parse_args()
    records = [audit(path) for path in sorted(Path(args.root).iterdir()) if (path / "gate.json").exists()]
    print(json.dumps({"verified_batches": len(records), "records": records}, indent=2))


if __name__ == "__main__":
    main()
