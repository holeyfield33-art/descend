"""Pre-formal base-model difficulty calibration; no hidden data or cloud calls."""
import argparse
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from descend.dsl import generate_dsl, grade
from descend.dsl.generator import generate_examples
from descend.registry import canonical_hash
from scripts.prepare_local_target import REVISION, WEIGHT_HASH, file_hash


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--target", required=True)
    args = parser.parse_args()
    if subprocess.check_output(["git", "status", "--porcelain"], text=True).strip():
        raise SystemExit("Calibration requires a clean commit")
    target = Path(args.target)
    if file_hash(target / "model.safetensors") != WEIGHT_HASH:
        raise SystemExit("Base weight identity mismatch")
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
    plan = {"label": "BASE DIFFICULTY CALIBRATION - NOT CLAIM-BEARING", "seed": 302,
            "revision": REVISION, "base_weight_hash": WEIGHT_HASH, "recipes": recipes,
            "selection_rule": "First listed recipe with dev accuracy between 0.25 and 0.60 inclusive",
            "hidden_evaluated": False, "cloud_cost_usd": 0, "formal_data": False,
            "git_sha": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
            "source_hash": file_hash(__file__), "dependency_lock_hash": file_hash("requirements-local-training-lock.txt")}
    (root / "plan.json").write_text(json.dumps(plan, indent=2), encoding="utf-8")
    (root / "source.py").write_bytes(Path(__file__).read_bytes())
    tokenizer = AutoTokenizer.from_pretrained(target, local_files_only=True, trust_remote_code=False)
    model = AutoModelForCausalLM.from_pretrained(target, local_files_only=True, trust_remote_code=False,
                use_safetensors=True, dtype=torch.float32, attn_implementation="eager")
    model.eval()
    records = []
    started = time.monotonic()
    for index, recipe in enumerate(recipes):
        system = ("Apply the requested string operations left to right. Return only the resulting string. "
                  "Operation definitions: " + json.dumps({op.name: op.primitive for op in dsl.operators}) +
                  ". rotate_left/right move one character; select_odd keeps indices 1,3,5; "
                  "select_even keeps indices 0,2,4; truncate keeps the first three characters; "
                  "swap_halves splits at floor(length/2).")
        if recipe["demonstrations"]:
            system += " Examples (input -> output): " + json.dumps([
                {"operators": [op.name], "string": "abcd", "output": op.fn("abcd")} for op in dsl.operators])
        examples = generate_examples(dsl, dsl.dev_templates, 2, 304,
                    min_len=recipe["length"], max_len=recipe["length"])
        predictions = []
        with torch.no_grad():
            for example in examples:
                if time.monotonic() - started > 1200:
                    raise RuntimeError("Calibration deadline exceeded")
                text = tokenizer.apply_chat_template([{"role": "system", "content": system},
                    {"role": "user", "content": example["input"]}], tokenize=False, add_generation_prompt=True)
                inputs = tokenizer(text, return_tensors="pt")
                generated = model.generate(**inputs, max_new_tokens=32, do_sample=False,
                                           pad_token_id=tokenizer.eos_token_id)
                answer = tokenizer.decode(generated[0, inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
                predictions.append({"input": example["input"], "output": answer})
        record = {"recipe": recipe, "system_prompt": system, "dataset": examples, "predictions": predictions,
                  "score": grade(predictions, examples), "dataset_hash": canonical_hash(examples)}
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
