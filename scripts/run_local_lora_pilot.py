"""Separate local real-weight feasibility pilot; no formal or hidden evaluation."""
import argparse
import importlib.metadata
import json
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from descend.dsl import generate_dsl, grade
from descend.dsl.generator import generate_examples
from descend.dsl.decoding import allowed_output_tokens
from descend.registry import canonical_hash
from scripts.prepare_local_target import TARGETS, file_hash


def write(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--steps", type=int, default=4)
    parser.add_argument("--seed", type=int, default=301)
    parser.add_argument("--length", type=int, default=6)
    parser.add_argument("--few-shot", action="store_true")
    parser.add_argument("--constrained", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.steps <= 16 or args.seed < 301 or not 2 <= args.length <= 6:
        raise SystemExit("Invalid local feasibility pilot limits")
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise SystemExit("Local pilot requires a clean canonical Git commit")
    target = Path(args.target)
    manifest = json.loads((target / "download_manifest.json").read_text())
    source = next((s for s in TARGETS.values() if s["model"] == manifest["model"] and s["revision"] == manifest["revision"]), None)
    if source is None or file_hash(target / "model.safetensors") != source["weight_hash"]:
        raise SystemExit("Target identity verification failed")
    if any(file_hash(target / name) != digest for name, digest in manifest["hashes"].items()):
        raise SystemExit("Target file changed since preparation")
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import LoraConfig, TaskType, get_peft_model, PeftModel
    torch.set_num_threads(2)
    torch.manual_seed(args.seed)
    torch.use_deterministic_algorithms(True)
    root = Path("artifacts/pilots/local-training") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root.mkdir(parents=True, exist_ok=False)
    start = time.monotonic()
    deadline = start + 1800
    def check_time():
        if time.monotonic() > deadline:
            raise RuntimeError("Local pilot wall-clock budget exceeded")
    plan = {"label": "LOCAL REAL-WEIGHT PILOT - NOT CLAIM-BEARING", "formal_data": False,
        "backend": "local_cpu", "token_factory_training": False, "agent": "scripted feasibility recipe",
        "model": source["model"], "revision": source["revision"], "base_weight_hash": source["weight_hash"],
        "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "source_hash": file_hash(Path(__file__)), "seed": args.seed, "steps": args.steps,
        "dependency_lock_hash": file_hash("requirements-local-training-lock.txt"),
        "device": "cpu", "threads": 2, "wall_clock_cap_sec": 1800, "cloud_cost_usd": 0,
        "training": {"lr": 0.0002, "lora_r": 8, "lora_alpha": 16, "dropout": 0,
                     "target_modules": ["q_proj", "v_proj"], "max_sequence_tokens": 512},
        "packages": {name: importlib.metadata.version(name) for name in ("torch", "transformers", "peft", "safetensors")}}
    plan["task_configuration"] = {"length": args.length, "few_shot": args.few_shot,
                                   "enable_thinking": False, "input_character_output_constraint": args.constrained}
    write(root / "plan.json", plan)
    snapshots = {}
    for tree in ("descend", "scripts"):
        for source in sorted(Path(tree).rglob("*.py")):
            destination = root / "code" / source
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
            snapshots[source.as_posix()] = file_hash(source)
    write(root / "source_snapshot.json", snapshots)
    plan["source_snapshot_hash"] = canonical_hash(snapshots)
    write(root / "plan.json", plan)
    write(root / "base_files.json", manifest)
    dsl = generate_dsl(args.seed)
    mapping = {op.name: op.primitive for op in dsl.operators}
    system = ("Apply the requested string operations from left to right. Return only the resulting string, "
              "without quotes or explanation. Operation names mean: " + json.dumps(mapping) +
              ". rotate_left/right move one character; select_odd keeps indices 1,3,5; "
              "select_even keeps indices 0,2,4; truncate keeps the first three characters; "
              "swap_halves splits at floor(length/2).")
    write(root / "system_prompt.json", {"content": system, "hash": canonical_hash(system)})
    demonstrations = []
    if args.few_shot:
        for op in dsl.operators:
            demonstrations.extend([{"role": "user", "content": json.dumps(
                {"operators": [op.name], "string": "abcd"}, sort_keys=True, separators=(",", ":"))},
                {"role": "assistant", "content": op.fn("abcd")}])
    write(root / "demonstration_messages.json", demonstrations)
    examples = generate_examples(dsl, dsl.train_templates, 2, args.seed + 99, min_len=args.length, max_len=args.length)
    random.Random(args.seed).shuffle(examples)
    training = examples[:8]
    dev = generate_examples(dsl, dsl.dev_templates, 1, args.seed + 2, min_len=args.length, max_len=args.length)[:4]
    write(root / "datasets.json", {"training": training, "dev": dev, "hidden_evaluated": False})
    tokenizer = AutoTokenizer.from_pretrained(target, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(target, local_files_only=True,
            trust_remote_code=False, use_safetensors=True, dtype=torch.float32, attn_implementation="eager")
    def prompt(example):
        return tokenizer.apply_chat_template([{"role": "system", "content": system}, *demonstrations,
            {"role": "user", "content": example["input"]}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
    def evaluate(current):
        current.eval()
        predictions = []
        with torch.no_grad():
            for example in dev:
                check_time()
                inputs = tokenizer(prompt(example), return_tensors="pt")
                kwargs = {}
                if args.constrained:
                    allowed = allowed_output_tokens(tokenizer, example["input"])
                    kwargs["prefix_allowed_tokens_fn"] = lambda batch, ids: allowed
                output = current.generate(**inputs, max_new_tokens=32, do_sample=False,
                                          pad_token_id=tokenizer.eos_token_id, **kwargs)
                text = tokenizer.decode(output[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
                predictions.append({"input": example["input"], "output": text})
        return {"score": grade(predictions, dev), "predictions": predictions}
    try:
        base = evaluate(model)
        write(root / "base_dev.json", base)
        print(json.dumps({"base_dev": base["score"]}), flush=True)
        adapted = get_peft_model(model, LoraConfig(task_type=TaskType.CAUSAL_LM,
            r=8, lora_alpha=16, lora_dropout=0, target_modules=["q_proj", "v_proj"]))
        optimizer = torch.optim.AdamW([p for p in adapted.parameters() if p.requires_grad], lr=0.0002)
        losses, tokens = [], 0
        adapted.train()
        for step in range(args.steps):
            check_time()
            example = training[step % len(training)]
            prefix = tokenizer(prompt(example), add_special_tokens=False)["input_ids"]
            answer = tokenizer(example["output"] + tokenizer.eos_token, add_special_tokens=False)["input_ids"]
            ids = prefix + answer
            if len(ids) > 512:
                raise RuntimeError("Training sequence cap exceeded")
            tokens += len(ids)
            labels = [-100] * len(prefix) + answer
            optimizer.zero_grad(set_to_none=True)
            loss = adapted(input_ids=torch.tensor([ids]), labels=torch.tensor([labels]), use_cache=False).loss
            if not torch.isfinite(loss):
                raise RuntimeError("Nonfinite training loss")
            loss.backward()
            optimizer.step()
            losses.append(float(loss.detach()))
            write(root / "training_progress.json", {"steps": len(losses), "losses": losses,
                "training_tokens": tokens, "example_indices": [i % len(training) for i in range(step + 1)]})
            print(json.dumps({"training_step": step + 1, "loss": losses[-1]}), flush=True)
        adapter_dir = root / "adapter"
        adapted.save_pretrained(adapter_dir, safe_serialization=True)
        hashes = {p.name: file_hash(p) for p in adapter_dir.iterdir() if p.is_file()}
        write(root / "candidate.json", {"base_weight_hash": source["weight_hash"], "adapter_files": hashes,
              "adapter_identity": canonical_hash(hashes), "training_dataset_hash": canonical_hash(training),
              "training_tokens": tokens, "steps": args.steps, "synthetic_adapter": False})
        after = evaluate(adapted)
        write(root / "adapted_dev.json", after)
        # Reload actual saved adapter bytes into the same frozen base for deployment-equivalence check.
        base_model = adapted.unload()
        reloaded = PeftModel.from_pretrained(base_model, adapter_dir, local_files_only=True)
        reload_result = evaluate(reloaded)
        if reload_result != after:
            raise RuntimeError("Saved adapter reload did not reproduce predictions")
        write(root / "result.json", {"status": "completed", "base_dev": base["score"],
            "adapted_dev": after["score"], "reload_verified": True, "hidden_evaluated": False,
            "cloud_cost_usd": 0, "elapsed_sec": time.monotonic() - start, "formal_data": False})
        print(json.dumps({"completed": str(root), "base": base["score"], "adapted": after["score"]}), flush=True)
    except Exception as exc:
        write(root / "result.json", {"status": "failed", "error_type": type(exc).__name__,
              "elapsed_sec": time.monotonic() - start, "formal_data": False})
        raise


if __name__ == "__main__":
    main()
