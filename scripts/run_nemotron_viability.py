"""Four autonomous real-Nemotron attempts with fake training, never claim data."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from descend.agents.nemotron import NemotronAgent
from descend.agents.prompts import SYSTEM_PROMPT, user_prompt
from descend.controller import Controller, BudgetState
from descend.controller.environment import load_controller_environment
from descend.controller.inference import TokenFactoryInference, NANO_MODEL_ID
from descend.controller.provenance import runtime_record, byte_hash
from descend.controller.spend import SpendLedger
from descend.registry import canonical_hash
from descend.sandbox.hard_isolation import isolation_available, run_in_hard_isolation
from scripts.prepare_tokenizer import prepare, TOKENIZER_HASH, REVISION, REPOSITORY


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def main():
    runtime = runtime_record()
    if runtime["worktree_dirty"]:
        raise SystemExit("Pilot requires a clean canonical Git commit")
    isolation = isolation_available()
    if not isolation["available"]:
        raise SystemExit("Linux namespace/chroot isolation is required; no paid call made")
    probe = run_in_hard_isolation(
        'import sys,json,os; print(json.dumps({"python":sys.version,"uid":os.getuid(),"gid":os.getgid()}))',
        workspace=Path("runs/runtime-probe/workspace"), controller_root=Path("controller_state"), timeout_sec=10)
    if not probe["ok"]:
        raise SystemExit("Isolated runtime probe failed; no paid call made")
    runtime["worker_runtime"] = json.loads(probe["stdout"])
    load_controller_environment()
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit("Missing controller API key")
    # Model selection uses authenticated catalog evidence, never a stale .env ID.
    catalog = json.loads(Path("controller_state/provider_preflight.json").read_text(encoding="utf-8"))
    models = catalog["checks"]["/v1/models"]["response"]["data"]
    if NANO_MODEL_ID not in {model["id"] for model in models}:
        raise SystemExit("Nano is absent from the authenticated catalog")
    from tokenizers import Tokenizer
    tokenizer = Tokenizer.from_file(str(prepare()))
    count_tokens = lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids)
    batch_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid4().hex[:8]
    root = Path("artifacts/pilots/viability") / batch_id
    root.mkdir(parents=True, exist_ok=False)
    ledger = SpendLedger("controller_state/cloud-spend.sqlite")
    client = TokenFactoryInference(api_key=key, ledger=ledger)
    controller = Controller(workspace_root="runs", controller_root="controller_state")
    plan = {"label": "PILOT — NOT CLAIM-BEARING", "phase": "2A", "batch_id": batch_id,
            "attempts": [{"arm": arm, "seed": seed} for arm, seed in zip("ABAB", (201, 202, 203, 204))],
            "go_rule": "At least 3 of 4 autonomous protocol completions", "runtime": runtime,
            "isolation": isolation, "agent_model": NANO_MODEL_ID, "target_model": "cpu-fake-target",
            "training_backend": "fake", "evaluation_backend": "synthetic hash score",
            "sampling": {"temperature": 0, "max_tokens": 4096, "seed": "attempt seed"},
            "tokenizer": {"repository": REPOSITORY, "revision": REVISION, "sha256": TOKENIZER_HASH},
            "system_prompt_hash": canonical_hash(SYSTEM_PROMPT), "formal_data": False}
    write(root / "plan.json", plan)
    results = []
    for attempt in plan["attempts"]:
        arm, seed = attempt["arm"], attempt["seed"]
        start = controller.start_run(arm, seed, budgets=BudgetState(actions_max=40,
                                     wall_clock_budget_sec=600, agent_token_budget=200_000))
        run_id = start["run_id"]
        state = controller._require(run_id)
        directory = root / run_id
        directory.mkdir()
        prompt = user_prompt(start["manifest"], reference_manifest=state.reference_manifest, count_tokens=count_tokens)
        reference_prompt = user_prompt(state.reference_manifest)
        record = {**attempt, "run_id": run_id, "runtime": runtime, "isolation": isolation,
                  "label": plan["label"], "manifest": start["manifest"], "manifest_hash": canonical_hash(start["manifest"]),
                  "input_content_tokens": count_tokens(prompt), "paired_a_content_tokens": count_tokens(reference_prompt),
                  "agent_model": NANO_MODEL_ID, "target_model": "cpu-fake-target", "budgets": state.budgets.as_dict(),
                  "hidden_seed_commitment": canonical_hash(state.hidden_seed), "claim_preregistration": None}
        write(directory / "manifest.json", record)
        print(json.dumps({"attempt_started": run_id, "arm": arm, "seed": seed}), flush=True)
        result = NemotronAgent(client, count_tokens=count_tokens).run(start["manifest"], controller, run_id, seed)
        if result["status"] == "completed":
            hidden = controller.hidden_eval(run_id)
            write(directory / "hidden_result.json", {"synthetic": True, **hidden})
        elif state.failure is None:
            controller._fail(run_id, "viability protocol incomplete")
        decision = controller.decide(run_id)
        write(directory / "decision.json", decision)
        write(directory / "transcript.json", state.transcript)
        write(directory / "datasets.json", state.datasets)
        write(directory / "budgets_final.json", state.budgets.as_dict())
        # Export frozen artifacts and anchored registry. Hidden generator seed stays private.
        committed = controller.roots.committed_path(run_id, "candidate.json").parent
        if committed.exists():
            import shutil
            shutil.copytree(committed, directory / "committed", dirs_exist_ok=True)
        log = controller.registry._path(run_id)
        for path in (log, log.with_suffix(".anchor.json")):
            (directory / path.name).write_bytes(path.read_bytes())
        valid, error = controller.registry.verify(run_id)
        verification = {"valid": valid, "error": error, "event_count": len(controller.registry.events(run_id)),
                        "log_hash": byte_hash(log), "anchor_hash": byte_hash(log.with_suffix(".anchor.json"))}
        write(directory / "registry_verification.json", verification)
        result.update(run_id=run_id, arm=arm, seed=seed, registry_valid=valid,
                      transcript_hash=canonical_hash(state.transcript))
        results.append(result)
        write(root / "results.json", {"label": plan["label"], "results": results,
                                      "cloud_accounting": ledger.summary()})
        print(json.dumps({"attempt_finished": result, "cloud_accounting": ledger.summary()}), flush=True)
        if not valid:
            raise SystemExit("Registry verification failed; pilot stopped")
        if result.get("category") == "infrastructure":
            raise SystemExit("External inference failed; attempts preserved, gate incomplete")
    completed = sum(result["status"] == "completed" for result in results)
    gate = {"label": plan["label"], "completed": completed, "attempts": 4, "go": completed >= 3,
            "cloud_accounting": ledger.summary(), "artifact_path": str(root), "runtime": runtime}
    write(root / "gate.json", gate)
    print(json.dumps(gate), flush=True)


if __name__ == "__main__":
    main()
