"""Controller — Zone 2 judge. Owns hidden data, evaluation, promotion, registry writes."""

from __future__ import annotations

import hashlib
import copy
import secrets
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

from descend.registry import RegistryStore, canonical_hash
from descend.dsl import generate_dsl, make_splits, grade
from descend.manifest import build_arm_a_manifest, build_arm_b_neutral
from descend.candidate import (
    build_candidate_identity,
    validate_candidate,
    STUB_BASE_HASH,
    STUB_EVALUATOR_HASH,
    STUB_CONTROLLER_HASH,
    STUB_PROMOTION_HASH,
)
from descend.evaluation.contamination import check_contamination
from descend.controller.budgets import BudgetState, BudgetExhausted
from descend.controller.promotion import evaluate_promotion


@dataclass
class RunState:
    run_id: str
    arm: str
    seed: int
    budgets: BudgetState
    dsl_seed: int
    hidden_seed: int = 0
    datasets: Dict[str, Any] = field(default_factory=dict)
    generated_examples: int = 0
    splits: Any = None
    dsl: Any = None
    candidate: Optional[Dict[str, Any]] = None
    candidate_committed: bool = False
    prediction: Optional[Dict[str, Any]] = None
    prediction_committed: bool = False
    contamination_flag: bool = False
    hidden_eval_done: bool = False
    decision: Optional[Dict[str, Any]] = None
    failure: Optional[str] = None
    transcript: List[Dict[str, Any]] = field(default_factory=list)


class Controller:
    """The judge. Agent cannot read or write its internals.

    Controller-owned state lives under controller_root (registry, hidden,
    committed artifacts). Agent workspace is a separate tree.
    """

    def __init__(
        self,
        registry: Optional[RegistryStore] = None,
        promotion_config: Optional[Dict[str, Any]] = None,
        workspace_root: str | Path = "./runs",
        controller_root: str | Path | None = None,
    ):
        from descend.sandbox.isolation import ControllerRoots
        self.workspace_root = Path(workspace_root)
        self.workspace_root.mkdir(parents=True, exist_ok=True)
        cr = Path(controller_root) if controller_root else (self.workspace_root.parent / "controller_state")
        self.roots = ControllerRoots(cr)
        self.registry = registry or RegistryStore(self.roots.registry)
        self.promotion_config = promotion_config or {}
        self._runs: Dict[str, RunState] = {}
        self._hidden_seeds: Dict[int, int] = {}

    def start_run(
        self,
        arm: str,
        seed: int,
        budgets: Optional[BudgetState] = None,
        target_evidence: Optional[Dict[str, Any]] = None,
        hidden_seed: Optional[int] = None,
    ) -> Dict[str, Any]:
        if arm not in ("A", "B", "C"):
            raise ValueError(f"Unknown arm: {arm}")
        run_id = f"dm0-{arm.lower()}-{seed}-{uuid4().hex[:8]}"
        budgets = copy.deepcopy(budgets) if budgets is not None else BudgetState()
        dsl = generate_dsl(seed)
        if hidden_seed is None:
            hidden_seed = self._hidden_seeds.setdefault(seed, secrets.randbits(128))
        # Private replay metadata is never returned through tools or registry views.
        self.roots.hidden.joinpath(f"{run_id}.seed").write_text(str(hidden_seed), encoding="utf-8")
        splits = make_splits(dsl, split_seed=seed, hidden_seed=hidden_seed)

        state = RunState(
            run_id=run_id,
            arm=arm,
            seed=seed,
            budgets=budgets,
            dsl_seed=seed,
            dsl=dsl,
            splits=splits,
            hidden_seed=hidden_seed,
        )
        self._runs[run_id] = state

        self.registry.append(
            "run_start",
            run_id,
            arm,
            seed,
            {
                "arm": arm,
                "seed": seed,
                "dsl_seed": seed,
                "budgets": budgets.as_dict(),
            },
        )

        # Issue manifest / neutral
        if arm == "A":
            evidence = target_evidence or {
                "target_checkpoint_id": "stub-base-v0",
                "target_checkpoint_hash": STUB_BASE_HASH,
                "architecture": "stub-transformer",
                "parameter_count": 1_000_000,
                "tokenizer_characteristics": {"vocab_size": 1000, "type": "char"},
                "adapter_compatibility": "lora-r8",
                "baseline_capability_profile": {"dev_acc": 0.25},
                "baseline_failure_profile": {"common_errors": ["truncation"]},
                "modification_lineage": [],
            }
            manifest = build_arm_a_manifest(target_evidence=evidence, budgets=budgets.as_dict())
        elif arm == "B":
            # Build a dummy A first for length matching
            dummy_a = build_arm_a_manifest(
                target_evidence={
                    "target_checkpoint_id": "x",
                    "target_checkpoint_hash": "0" * 64,
                    "architecture": "x",
                    "parameter_count": 0,
                    "tokenizer_characteristics": {},
                    "adapter_compatibility": "x",
                    "baseline_capability_profile": {},
                    "baseline_failure_profile": {},
                    "modification_lineage": [],
                },
                budgets=budgets.as_dict(),
            )
            manifest = build_arm_b_neutral(arm_a_manifest=dummy_a, budgets=budgets.as_dict())
        else:
            manifest = {"arm": "C", "note": "scripted baseline; no agent"}

        self.registry.append(
            "manifest_issued",
            run_id,
            arm,
            seed,
            {"manifest_hash": canonical_hash(manifest), "arm": arm},
        )
        return {
            "run_id": run_id,
            "manifest": manifest,
            "operational_only": True,  # hidden data never included
        }

    def create_dataset(
        self,
        run_id: str,
        examples: List[Dict[str, str]],
        source: str = "agent",
    ) -> Dict[str, Any]:
        state = self._require(run_id)
        self._optimization_open(state)
        state.budgets.record_action()
        if state.generated_examples + len(examples) > 100:
            state.budgets.breached = True
            raise BudgetExhausted("generation budget exhausted")
        examples = copy.deepcopy(examples)
        state.generated_examples += len(examples)
        ds_hash = canonical_hash(examples)
        state.datasets[ds_hash] = examples
        # Contamination check against hidden
        contam = check_contamination(examples, state.splits.hidden)
        if contam["contaminated"]:
            state.contamination_flag = True
        self.registry.append(
            "dataset_created",
            run_id,
            state.arm,
            state.seed,
            {
                "dataset_hash": ds_hash,
                "n_examples": len(examples),
                "source": source,
                "contamination": {"passed": not contam["contaminated"]},
            },
        )
        return {"dataset_hash": ds_hash, "contamination": {"passed": not contam["contaminated"]}}

    def submit_training(
        self,
        run_id: str,
        dataset_hash: str,
        config: Dict[str, Any],
        fake_backend_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        state = self._require(run_id)
        self._optimization_open(state)
        if dataset_hash not in state.datasets:
            raise ValueError("unknown dataset")
        config = copy.deepcopy(config)
        epochs = config.get("epochs", 1)
        if type(epochs) is not int or not 1 <= epochs <= 10:
            raise ValueError("invalid training epochs")
        state.budgets.record_tokens(sum(len(e["input"]) + len(e["output"])
                                       for e in state.datasets[dataset_hash]) * epochs, training=True)
        try:
            state.budgets.record_training()
        except BudgetExhausted as e:
            self._fail(run_id, str(e))
            raise

        self.registry.append(
            "training_submitted",
            run_id,
            state.arm,
            state.seed,
            {"dataset_hash": dataset_hash, "config": config},
        )

        # Fake backend
        result = fake_backend_result or _fake_train(dataset_hash, config, state.seed)
        self.registry.append(
            "training_completed",
            run_id,
            state.arm,
            state.seed,
            result,
        )

        if result.get("status") == "success":
            cand = {
                "adapter_id": result["adapter_id"],
                "adapter_hash": result["adapter_hash"],
                "training_dataset_hash": dataset_hash,
                "training_config": config,
                "status": "ok",
            }
            state.candidate = cand
            self.registry.append(
                "candidate_created",
                run_id,
                state.arm,
                state.seed,
                {"adapter_id": cand["adapter_id"], "adapter_hash": cand["adapter_hash"]},
            )
        else:
            state.failure = result.get("reason", "training_failed")
            self.registry.append(
                "run_failure",
                run_id,
                state.arm,
                state.seed,
                {"category": "agent", "reason": state.failure},
            )
        return result

    def commit_candidate(self, run_id: str, transcript_hash: str = "") -> Dict[str, Any]:
        state = self._require(run_id)
        if state.candidate is None:
            raise RuntimeError("No candidate to commit")
        if state.candidate_committed:
            raise RuntimeError("Candidate already committed")
        state.budgets.record_action()

        ok, reasons = validate_candidate(state.candidate)
        if not ok:
            self._fail(run_id, f"invalid candidate: {reasons}")
            raise RuntimeError(f"invalid candidate: {reasons}")

        identity = build_candidate_identity(
            base_hash=STUB_BASE_HASH,
            adapter_hash=state.candidate["adapter_hash"],
            training_dataset_hash=state.candidate["training_dataset_hash"],
            training_config_hash=canonical_hash(state.candidate["training_config"]),
            agent_transcript_hash=transcript_hash or canonical_hash(state.transcript),
            evaluator_code_hash=STUB_EVALUATOR_HASH,
            controller_code_hash=STUB_CONTROLLER_HASH,
            promotion_rule_hash=STUB_PROMOTION_HASH,
        )
        state.candidate["identity"] = identity
        # TOCTOU: freeze committed bytes into controller-owned immutable storage
        import json as _json
        frozen = {
            "adapter_hash": state.candidate["adapter_hash"],
            "adapter_id": state.candidate["adapter_id"],
            "training_dataset_hash": state.candidate["training_dataset_hash"],
            "training_config": state.candidate["training_config"],
            "identity": identity,
        }
        dest = self.roots.committed_path(run_id, "candidate.json")
        dest.write_text(_json.dumps(frozen, sort_keys=True), encoding="utf-8")
        state.candidate["_frozen_path"] = str(dest)
        state.candidate["_frozen_hash"] = canonical_hash(frozen)
        state.candidate_committed = True
        self.registry.append(
            "candidate_committed",
            run_id,
            state.arm,
            state.seed,
            {
                "identity": identity,
                "adapter_id": state.candidate["adapter_id"],
                "frozen_hash": state.candidate["_frozen_hash"],
            },
        )
        return identity

    def commit_prediction(self, run_id: str, prediction: Dict[str, Any]) -> Dict[str, Any]:
        state = self._require(run_id)
        required = {
            "predicted_target_delta",
            "interval_low",
            "interval_high",
            "predicted_regression_deltas",
            "rationale",
        }
        missing = required - set(prediction.keys())
        if missing:
            raise ValueError(f"Prediction missing fields: {missing}")
        import math
        if set(prediction) != required:
            raise ValueError("unexpected prediction fields")
        values = [prediction[k] for k in ("predicted_target_delta", "interval_low", "interval_high")]
        if not isinstance(prediction["predicted_regression_deltas"], dict):
            raise ValueError("invalid regression prediction")
        values.extend(prediction["predicted_regression_deltas"].values())
        if any(type(v) not in (int, float) or not math.isfinite(v) for v in values):
            raise ValueError("prediction must contain finite numbers")
        if prediction["interval_low"] > prediction["interval_high"] or not isinstance(prediction["rationale"], str):
            raise ValueError("invalid prediction interval or rationale")
        if state.prediction_committed:
            raise RuntimeError("Prediction already committed; immutable")
        if not state.candidate_committed:
            raise RuntimeError("Prediction requires committed candidate")
        state.budgets.record_action()
        prediction = copy.deepcopy(prediction)

        pred_hash = canonical_hash(prediction)
        state.prediction = prediction
        # TOCTOU: freeze prediction into controller-owned storage
        import json as _json
        dest = self.roots.committed_path(run_id, "prediction.json")
        dest.write_text(_json.dumps(prediction, sort_keys=True), encoding="utf-8")
        state.prediction["_frozen_path"] = str(dest)
        state.prediction["_frozen_hash"] = pred_hash
        state.prediction_committed = True
        self.registry.append(
            "prediction_committed",
            run_id,
            state.arm,
            state.seed,
            {"prediction_hash": pred_hash, "prediction": prediction},
        )
        return {"prediction_hash": pred_hash}

    def hidden_eval(self, run_id: str) -> Dict[str, Any]:
        state = self._require(run_id)
        if not state.candidate_committed:
            raise RuntimeError("Hidden eval requires committed candidate")
        if not state.prediction_committed:
            raise RuntimeError("Hidden eval requires committed prediction")
        # TOCTOU: re-verify frozen artifacts match committed hashes
        self._verify_frozen_artifacts(state)
        if state.hidden_eval_done:
            raise RuntimeError("Hidden eval already performed (one-shot)")

        # Fake scoring: deterministic function of adapter hash + seed
        adapter_h = state.candidate["adapter_hash"]
        score = _fake_hidden_score(adapter_h, state.seed)
        baseline = 0.25
        delta = score - baseline

        # Regression (fake)
        reg = {"reg_shallow": max(0.0, baseline - 0.02)}

        result = {
            "hidden_accuracy": score,
            "baseline": baseline,
            "target_delta": delta,
            "regression": reg,
        }
        state.hidden_eval_done = True
        self.registry.append(
            "hidden_eval",
            run_id,
            state.arm,
            state.seed,
            result,
        )
        return result

    def decide(self, run_id: str) -> Dict[str, Any]:
        state = self._require(run_id)
        if state.decision is not None:
            raise RuntimeError("run already decided")
        if not state.hidden_eval_done:
            # Force zero-gain path if never evaluated
            if state.failure or not state.candidate_committed:
                decision = {
                    "decision": "REJECT",
                    "reasons": [{"criterion": "no_valid_candidate", "passed": False}],
                    "target_delta": 0.0,
                    "predicted_delta": 0.0,
                }
            else:
                raise RuntimeError("Must run hidden_eval before decide")
        else:
            # Retrieve last hidden_eval payload
            evs = self.registry.events(run_id)
            hidden = next(e for e in reversed(evs) if e["event_type"] == "hidden_eval")
            delta = hidden["payload"]["target_delta"]
            self._verify_frozen_artifacts(state)
            import json
            pred = json.loads(Path(state.prediction["_frozen_path"]).read_text(encoding="utf-8"))
            decision = evaluate_promotion(
                candidate_valid=state.candidate is not None and not state.failure,
                target_delta=delta,
                predicted_delta=float(pred.get("predicted_target_delta", 0)),
                interval_low=float(pred.get("interval_low", -1)),
                interval_high=float(pred.get("interval_high", 1)),
                regression_deltas=hidden["payload"].get("regression", {}),
                contamination_flag=state.contamination_flag,
                budgets_respected=state.budgets.respected(),
                candidate_committed=state.candidate_committed,
                prediction_committed=state.prediction_committed,
                config=self.promotion_config,
            )
        state.decision = decision
        self.registry.append(
            "decision",
            run_id,
            state.arm,
            state.seed,
            decision,
        )
        self.registry.append(
            "run_end",
            run_id,
            state.arm,
            state.seed,
            {"decision": decision["decision"]},
        )
        return decision

    def get_dev_examples(self, run_id: str) -> List[Dict[str, str]]:
        """Agent may request dev examples (budgeted elsewhere)."""
        state = self._require(run_id)
        self._optimization_open(state)
        state.budgets.record_dev_eval()
        return list(state.splits.dev)

    def dev_eval(self, run_id: str) -> Dict[str, float]:
        """Capped fake dev scoring; no hidden split is consulted."""
        state = self._require(run_id)
        self._optimization_open(state)
        if state.candidate is None:
            raise RuntimeError("no candidate to evaluate")
        state.budgets.record_dev_eval()
        result = {"dev_accuracy": _fake_hidden_score(state.candidate["adapter_hash"], state.dsl_seed + 1)}
        self.registry.append("dev_eval", run_id, state.arm, state.seed, result)
        return result

    def _optimization_open(self, state: RunState) -> None:
        if state.candidate_committed or state.hidden_eval_done or state.decision or state.failure:
            raise RuntimeError("optimization is closed")
        state.budgets.check()

    def read_registry(self, run_id: str):
        state = self._require(run_id)
        if state.hidden_eval_done or state.decision:
            raise RuntimeError("agent session closed")
        state.budgets.record_action()
        return self.registry.read_only_view(run_id, state.arm)

    def get_train_generator_policy(self, run_id: str) -> Dict[str, Any]:
        """What the agent is allowed to request from the budgeted generator."""
        state = self._require(run_id)
        return {
            "allowed_depths": [1, 2],  # never hidden depths
            "max_examples": 100,
            "max_training_tokens": state.budgets.max_training_tokens,
            "note": "Hidden-depth templates are never available to the agent.",
        }


    def _verify_frozen_artifacts(self, state: RunState) -> None:
        """Recompute hashes of controller-owned frozen files; detect post-commit mutation."""
        import json as _json
        cand_path = Path(state.candidate.get("_frozen_path", ""))
        if not cand_path.is_file():
            raise RuntimeError("TOCTOU: frozen candidate missing")
        loaded = _json.loads(cand_path.read_text(encoding="utf-8"))
        if canonical_hash(loaded) != state.candidate.get("_frozen_hash"):
            raise RuntimeError("TOCTOU: frozen candidate hash mismatch")
        if loaded.get("adapter_hash") != state.candidate.get("adapter_hash"):
            raise RuntimeError("TOCTOU: adapter hash mutated after commit")
        pred_path = Path(state.prediction.get("_frozen_path", ""))
        if not pred_path.is_file():
            raise RuntimeError("TOCTOU: frozen prediction missing")
        pred_loaded = _json.loads(pred_path.read_text(encoding="utf-8"))
        # strip internal keys if any leaked
        clean = {k: v for k, v in pred_loaded.items() if not k.startswith("_")}
        if canonical_hash(clean) != state.prediction.get("_frozen_hash"):
            raise RuntimeError("TOCTOU: frozen prediction hash mismatch")

    def _require(self, run_id: str) -> RunState:
        if run_id not in self._runs:
            raise KeyError(f"Unknown run_id: {run_id}")
        return self._runs[run_id]

    def _fail(self, run_id: str, reason: str, category: str = "agent") -> None:
        state = self._runs[run_id]
        state.failure = reason
        self.registry.append(
            "run_failure",
            run_id,
            state.arm,
            state.seed,
            {"category": category, "reason": reason},
        )


def _fake_train(dataset_hash: str, config: Dict[str, Any], seed: int) -> Dict[str, Any]:
    """Deterministic fake training backend."""
    material = f"{dataset_hash}:{canonical_hash(config)}:{seed}"
    h = hashlib.sha256(material.encode()).hexdigest()
    # Simulate occasional failure
    if config.get("force_fail"):
        return {"status": "failure", "reason": "forced_failure"}
    adapter_id = f"adapter-{h[:12]}"
    return {
        "status": "success",
        "adapter_id": adapter_id,
        "adapter_hash": h,
        "epochs": config.get("epochs", 1),
    }


def _fake_hidden_score(adapter_hash: str, seed: int) -> float:
    """Deterministic score in [0, 1] from adapter hash + seed."""
    material = f"{adapter_hash}:{seed}"
    h = hashlib.sha256(material.encode()).hexdigest()
    # Map first 8 hex digits to [0.1, 0.9]
    val = int(h[:8], 16) / 0xFFFFFFFF
    return 0.1 + 0.8 * val
