"""Verify archived local training evidence without loading a model or credentials."""
import argparse
import json
import struct
from pathlib import Path

from descend.dsl import grade
from descend.registry import canonical_hash
from scripts.prepare_local_target import file_hash, TARGETS


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def inspect_adapter(path):
    data = Path(path).read_bytes()
    header_size = struct.unpack_from("<Q", data)[0]
    assert header_size < len(data) - 8
    header = json.loads(data[8:8 + header_size])
    counts = {}
    for name, tensor in header.items():
        if "lora_B" not in name:
            continue
        assert tensor["dtype"] == "F32"
        low, high = tensor["data_offsets"]
        payload = data[8 + header_size + low:8 + header_size + high]
        assert len(payload) == high - low
        counts[name] = sum(value != 0 for value, in struct.iter_unpack("<f", payload))
    assert counts and sum(counts.values()) > 0
    return {"lora_B_tensors": len(counts), "nonzero_lora_B_values": sum(counts.values())}


def audit(root):
    if not __debug__:
        raise RuntimeError("Audit requires assertions enabled")
    root = Path(root)
    plan, result = read(root / "plan.json"), read(root / "result.json")
    assert not plan["formal_data"] and not plan["token_factory_training"]
    source = next(s for s in TARGETS.values() if s["model"] == plan["model"] and s["revision"] == plan["revision"])
    assert plan["base_weight_hash"] == source["weight_hash"] and plan["cloud_cost_usd"] == 0
    snapshots = read(root / "source_snapshot.json")
    assert canonical_hash(snapshots) == plan["source_snapshot_hash"]
    assert all(file_hash(root / "code" / name) == digest for name, digest in snapshots.items())
    assert file_hash(root / "code/scripts/run_local_lora_pilot.py") == plan["source_hash"]
    candidate = read(root / "candidate.json")
    assert all(file_hash(root / "adapter" / name) == digest for name, digest in candidate["adapter_files"].items())
    assert canonical_hash(candidate["adapter_files"]) == candidate["adapter_identity"]
    datasets = read(root / "datasets.json")
    assert canonical_hash(datasets["training"]) == candidate["training_dataset_hash"]
    progress = read(root / "training_progress.json")
    assert progress["steps"] == len(progress["losses"]) == candidate["steps"] == plan["steps"]
    assert progress["training_tokens"] == candidate["training_tokens"]
    for name, key in (("base_dev.json", "base_dev"), ("adapted_dev.json", "adapted_dev")):
        evaluation = read(root / name)
        assert evaluation["score"] == grade(evaluation["predictions"], datasets["dev"]) == result[key]
    assert result["reload_verified"] and not result["hidden_evaluated"]
    inspection = inspect_adapter(root / "adapter/adapter_model.safetensors")
    return {"verified": True, "backend": "local_cpu", "formal_data": False,
            "base_dev": result["base_dev"], "adapted_dev": result["adapted_dev"],
            "reload_verified": True, "steps": progress["steps"], "training_tokens": progress["training_tokens"],
            "adapter_inspection": inspection}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root")
    print(json.dumps(audit(parser.parse_args().root), indent=2))
