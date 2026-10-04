"""Download a pinned public target as data; no credentials or remote code."""
import hashlib
import json
import urllib.request
from pathlib import Path

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
WEIGHT_HASH = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"
TARGETS = {
    "qwen2.5-0.5b": {"model": MODEL, "revision": REVISION, "weight_hash": WEIGHT_HASH,
                     "weight_size": 988097824},
    "qwen3-0.6b": {"model": "Qwen/Qwen3-0.6B", "revision": "c1899de289a04d12100db370d81485cdf75e47ca",
                   "weight_hash": "f47f71177f32bcd101b7573ec9171e6a57f4f4d31148d38e382306f42996874b",
                   "weight_size": 1503300328},
}
FILES = ("config.json", "generation_config.json", "model.safetensors", "tokenizer.json",
         "tokenizer_config.json", "vocab.json", "merges.txt", "LICENSE")


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare(destination, *, model="qwen2.5-0.5b"):
    source = TARGETS[model]
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in FILES:
        path = destination / name
        if not path.exists():
            temporary = path.with_suffix(path.suffix + ".partial")
            url = f"https://huggingface.co/{source['model']}/resolve/{source['revision']}/{name}"
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                total = 0
                while block := response.read(1024 * 1024):
                    total += len(block)
                    if total > (source["weight_size"] if name == "model.safetensors" else 25_000_000):
                        raise RuntimeError("Target download size cap exceeded")
                    output.write(block)
            temporary.replace(path)
        hashes[name] = file_hash(path)
        if name == "model.safetensors" and (hashes[name] != source["weight_hash"] or path.stat().st_size != source["weight_size"]):
            raise RuntimeError("Pinned target weight verification failed")
        print(json.dumps({"verified_file": name, "sha256": hashes[name]}), flush=True)
    (destination / "download_manifest.json").write_text(json.dumps({"model": source["model"],
        "revision": source["revision"], "hashes": hashes}, indent=2), encoding="utf-8")
    return destination


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    parser.add_argument("--model", choices=TARGETS, default="qwen2.5-0.5b")
    args = parser.parse_args()
    prepare(args.destination, model=args.model)
