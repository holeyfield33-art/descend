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
