"""Two bounded inference calls to check initial A/B provider prompt usage."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from descend.agents.prompts import SYSTEM_PROMPT, user_prompt
from descend.controller import Controller, BudgetState
from descend.controller.environment import load_controller_environment
from descend.controller.inference import TokenFactoryInference, SUPER_MODEL_ID
from descend.controller.provenance import runtime_record
from descend.controller.spend import SpendLedger
from descend.registry import canonical_hash
from scripts.prepare_tokenizer import prepare


def main():
    runtime = runtime_record()
    if runtime["worktree_dirty"]:
        raise SystemExit("Calibration requires a clean canonical commit")
    load_controller_environment()
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(prepare(model="super")))
    count = lambda content: len(tokenizer.encode(content, add_special_tokens=False).ids)
    ledger = SpendLedger("controller_state/cloud-spend.sqlite")
    inference = TokenFactoryInference(api_key=os.environ["NEBIUS_API_KEY"], ledger=ledger, model=SUPER_MODEL_ID)
    controller = Controller(workspace_root="runs", controller_root="controller_state")
    records = []
    root = Path("artifacts/pilots/length-calibration") / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    root.mkdir(parents=True, exist_ok=False)
    try:
        for arm in "AB":
            start = controller.start_run(arm, 401, budgets=BudgetState(agent_token_budget=100_000))
            state = controller._require(start["run_id"])
            content = user_prompt(start["manifest"], reference_manifest=state.reference_manifest, count_tokens=count)
            evidence = inference.complete([{"role": "system", "content": SYSTEM_PROMPT},
                                           {"role": "user", "content": content}], state, seed=401, max_tokens=1)
            records.append({"arm": arm, "input_content_tokens": count(content),
                            "input_hash": canonical_hash(content), "evidence": evidence})
    finally:
        summary = {"label": "PROVIDER LENGTH CALIBRATION - NOT A PROTOCOL OR FORMAL RUN",
                   "runtime": runtime, "records": records, "cloud_accounting": ledger.summary()}
        if len(records) == 2:
            counts = [r["evidence"]["response"]["usage"]["prompt_tokens"] for r in records]
            summary.update(provider_prompt_tokens=counts, matched=counts[0] == counts[1])
            summary.update(provider_prompt_token_difference=abs(counts[0] - counts[1]),
                           proposed_tolerance_tokens=1, within_proposed_tolerance=abs(counts[0] - counts[1]) <= 1)
        (root / "calibration.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
        print(json.dumps({k: v for k, v in summary.items() if k not in {"runtime", "records"}}))


if __name__ == "__main__":
    main()
