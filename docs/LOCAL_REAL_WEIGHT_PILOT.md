# Local real-weight feasibility pilot

The user requested the best choice and continued progress within the $20 cloud ceiling. Qwen2.5-0.5B-Instruct is the selected first target: it is the smallest instruct model in the [documented Nebius LoRA list](https://docs.tokenfactory.nebius.com/post-training/models), and its [official model card](https://huggingface.co/Qwen/Qwen2.5-0.5B-Instruct) supplies a standard Transformers inference example and Apache 2.0 license.

Account-specific small-target deployment and training prices remain unverified. A separate **local CPU feasibility pilot** uses real public weights and PEFT LoRA, at zero additional cloud spend. It does not establish the requested Token Factory job/deployment pipeline, does not replace the original study silently, and does not supply formal DM0 data. The local recipe follows the [official PEFT quicktour](https://huggingface.co/docs/peft/quicktour); the unchanged Nebius cookbook remains the primary reference for cloud integration.

Target revision: `7ae557604adf67be50417f59c2c2f167def9a775`. Safetensors SHA-256: `fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe`. Downloads are public data only, with no credentials or remote Python code. Base files are hashed and checked before model loading. Large base weights stay in the controller's cache.

The pilot uses eight training examples, four dev examples, rank-8 LoRA on query/value projections, four optimizer steps, CPU execution with two threads, deterministic greedy evaluation and a 30-minute outer deadline. Saved adapter files, dataset/configuration, source bytes, actual package versions, losses, dev predictions and reload verification are recorded under `artifacts/pilots/local-training/`. No hidden evaluation is performed. Low or unchanged accuracy is retained honestly.

## Task-definition correction

Prior generator inputs contained only random source strings while output generation depended on an omitted operator sequence. That is ambiguous for a real target model. Inputs now contain canonical JSON with `operators` and `string`, preserving the seeded task family and left-to-right transformations. This is an explicit pre-formal protocol revision. Prior archived fake-backend viability records remain unchanged and continue to support protocol-operation claims only.

Grading now counts each unique prediction once and rejects conflicting outputs for one task input. Duplicate predictions cannot push accuracy above one.

## Reproduction

Use a separate Linux environment. Install the CPU PyTorch wheel from `https://download.pytorch.org/whl/cpu`, then the exact packages in `requirements-local-training-lock.txt`; this additional lock is separate from the lightweight controller/test runtime. Run from a clean canonical checkout:

```bash
python -m scripts.prepare_local_target /path/to/controller-cache/qwen-0.5b
timeout 1800 python -m scripts.run_local_lora_pilot --target /path/to/controller-cache/qwen-0.5b
```

This pilot is scripted feasibility work. Real Nemotron-controlled training, task calibration, hidden evaluation and 12 paired formal seeds remain subsequent gates.

## Recorded results and target escalation

Qwen2.5-0.5B-Instruct completed a real four-step LoRA pilot at `artifacts/pilots/local-training/20261004T171319Z`, implementation `62de26823a62759219c0a5d77d4a7484d3f1b67e`. It processed 690 measured training tokens and saved actual safetensors adapter weights. Base and adapted dev accuracy were both **0/4**; reload reproduced the adapted predictions exactly. The audit found 48 LoRA-B tensors with 196,608 nonzero values, consistent with updates from their zero initialization. This proves local execution and serialization, not useful adaptation.

Base difficulty calibration at seed 302 scored **10%, 0%, 0%** for the three declared recipes. Conversational demonstrations then scored **10%, 0%**. All results remain under `artifacts/pilots/local-calibration/`; none met the predeclared 25–60% range. Qwen2.5-0.5B is therefore unsuitable for the tested task/prompt conditions so far.

The second tested candidate was `Qwen/Qwen3-0.6B`, also in the documented LoRA list, with revision `c1899de289a04d12100db370d81485cdf75e47ca`, weight SHA-256 `f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b`. Its [official card](https://huggingface.co/Qwen/Qwen3-0.6B) documents `enable_thinking=False` for direct answers. At seed 302, three base recipes scored **0/10 each** without a decoder constraint (`20261004T172814Z`) and **0/10 each** with an input-character output constraint (`20261004T173431Z`). The constraint permits only characters present in the task input, as every DSL operation selects, reorders or duplicates those characters. It uses neither expected answers nor hidden examples. The constrained model mostly copied the source string; it did not produce empty answers. These are preserved failed calibration pilots, not formal results. No target or recipe met the 25–60% gate, and no formal target choice has been frozen.

Audit the saved real-weight pilot without loading weights or credentials:

```bash
python -m scripts.audit_local_pilot artifacts/pilots/local-training/20261004T171319Z
```
