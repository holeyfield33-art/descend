"""Pre-formal base-model difficulty calibration; no hidden data or cloud calls."""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from descend.dsl import generate_dsl, grade
from descend.dsl.generator import generate_examples
from descend.dsl.decoding import allowed_output_tokens
from descend.registry import canonical_hash
from scripts.prepare_local_target import TARGETS, file_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    parser.add_argument("--few-shot", action="store_true")
    parser.add_argument("--constrained", action="store_true")
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise SystemExit("Calibration requires a clean commit")
    target = Path(args.target)
    metadata = json.loads((target / "download_manifest.json").read_text())
    source = next((s for s in TARGETS.values() if s["model"] == metadata["model"] and s["revision"] == metadata["revision"]), None)
    if source is None or file_hash(target / "model.safetensors") != source["weight_hash"]:
        raise SystemExit("Base weight identity mismatch")
    if any(file_hash(target / name) != digest for name, digest in metadata["hashes"].items()):
        raise SystemExit("Target file identity mismatch")
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer
    torch.set_num_threads(2)
    torch.manual_seed(302)
    torch.use_deterministic_algorithms(True)
    root = Path("artifacts/pilots/local-calibration") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root.mkdir(parents=True, exist_ok=False)
    dsl = generate_dsl(302)
    recipes = [{"length": 2, "demonstrations": False}, {"length": 4, "demonstrations": True},
               {"length": 6, "demonstrations": True}]
    if args.few_shot:
        recipes = [{"length": 2, "demonstrations": False}, {"length": 4, "demonstrations": False}]
    plan = {"label": "BASE DIFFICULTY CALIBRATION - NOT CLAIM-BEARING", "seed": 302,
            "model": source["model"], "revision": source["revision"], "base_weight_hash": source["weight_hash"], "recipes": recipes,
            "selection_rule": "First listed recipe with dev accuracy between 0.25 and 0.60 inclusive",
            "hidden_evaluated": False, "cloud_cost_usd": 0, "formal_data": False,
            "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "source_hash": file_hash(__file__), "dependency_lock_hash": file_hash("requirements-local-training-lock.txt")}
    plan["few_shot_chat_demonstrations"] = args.few_shot
    plan["input_character_output_constraint"] = args.constrained
    (root / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (root / "source.py").write_bytes(Path(__file__).read_bytes())
    tokenizer = AutoTokenizer.from_pretrained(target, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(target, local_files_only=True, trust_remote_code=False,
                use_safetensors=True, dtype=torch.float32, attn_implementation="eager")
    model.eval()
    records = []
    started = time.monotonic()
    sanity = []
    for question in ("What is 2 + 2? Return only the number.", "Reverse abc. Return only the reversed string."):
        text = tokenizer.apply_chat_template([{"role": "user", "content": question}],
                                              tokenize=False, add_generation_prompt=True, enable_thinking=False)
        inputs = tokenizer(text, return_tensors="pt")
        with torch.no_grad():
            generated = model.generate(**inputs, max_new_tokens=16, do_sample=False,
                                       pad_token_id=tokenizer.eos_token_id)
        sanity.append({"prompt": question, "answer": tokenizer.decode(
            generated[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()})
    (root / "sanity.json").write_text(json.dumps(sanity, indent=2), encoding="utf-8")
    for index, recipe in enumerate(recipes):
        system = ("Apply the requested string operations left to right. Return only the resulting string. "
                  "Operation definitions: " + json.dumps({op.name: op.primitive for op in dsl.operators}) +
                  ". rotate_left/right move one character; select_odd keeps indices 1,3,5; "
                  "select_even keeps indices 0,2,4; truncate keeps the first three characters; "
                  "swap_halves splits at floor(length/2).")
        if recipe["demonstrations"]:
            system += " Examples (input -> output): " + json.dumps([
                {"operators": [op.name], "string": "abcd", "output": op.fn("abcd")} for op in dsl.operators])
        demonstration_messages = []
        if args.few_shot:
            for op in dsl.operators:
                demonstration_messages.extend([{"role": "user", "content": json.dumps(
                    {"operators": [op.name], "string": "abcd"}, sort_keys=True, separators=(",", ":"))},
                    {"role": "assistant", "content": op.fn("abcd")}])
        examples = generate_examples(dsl, dsl.dev_templates, 2, 304,
                    min_len=recipe["length"], max_len=recipe["length"])
        predictions = []
        with torch.no_grad():
            for example in examples:
                if time.monotonic() - started > 1200:
                    raise RuntimeError("Calibration deadline exceeded")
                text = tokenizer.apply_chat_template([{"role": "system", "content": system}, *demonstration_messages,
                    {"role": "user", "content": example["input"]}], tokenize=False, add_generation_prompt=True, enable_thinking=False)
                inputs = tokenizer(text, return_tensors="pt")
                kwargs = {}
                if args.constrained:
                    allowed = allowed_output_tokens(tokenizer, example["input"])
                    kwargs["prefix_allowed_tokens_fn"] = lambda batch, ids: allowed
                generated = model.generate(**inputs, max_new_tokens=32, do_sample=False,
                                           pad_token_id=tokenizer.eos_token_id, **kwargs)
                answer = tokenizer.decode(generated[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
                predictions.append({"input": example["input"], "output": answer})
        record = {"recipe": recipe, "system_prompt": system, "dataset": examples, "predictions": predictions,
                  "score": grade(predictions, examples), "dataset_hash": canonical_hash(examples),
                  "demonstration_messages": demonstration_messages}
        records.append(record)
        (root / f"recipe-{index}.json").write_text(json.dumps(record, indent=2), encoding="utf-8")
        print(json.dumps({"recipe": recipe, "score": record["score"]}), flush=True)
    selected = next((i for i, r in enumerate(records) if 0.25 <= r["score"]["accuracy"] <= 0.60), None)
    result = {"status": "completed", "selected_recipe": selected,
              "scores": [r["score"] for r in records], "elapsed_sec": time.monotonic() - started,
              "hidden_evaluated": False, "formal_data": False}
    (root / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
