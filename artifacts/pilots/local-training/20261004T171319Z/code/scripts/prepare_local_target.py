"""Download a pinned public target as data; no credentials or remote code."""
import hashlib
import json
import urllib.request
from pathlib import Path

MODEL = "Qwen/Qwen2.5-0.5B-Instruct"
REVISION = "7ae557604adf67be50417f59c2c2f167def9a775"
WEIGHT_HASH = "fdf756fa7fcbe7404d5c60e26bff1a0c8b8aa1f72ced49e7dd0210fe288fb7fe"
FILES = ("config.json", "generation_config.json", "model.safetensors", "tokenizer.json",
         "tokenizer_config.json", "vocab.json", "merges.txt", "LICENSE")


def file_hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def prepare(destination):
    destination = Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    hashes = {}
    for name in FILES:
        path = destination / name
        if not path.exists():
            temporary = path.with_suffix(path.suffix + ".partial")
            url = f"https://huggingface.co/{MODEL}/resolve/{REVISION}/{name}"
            with urllib.request.urlopen(url, timeout=60) as response, temporary.open("wb") as output:
                total = 0
                while block := response.read(1024 * 1024):
                    total += len(block)
                    if total > 1_100_000_000:
                        raise RuntimeError("Target download size cap exceeded")
                    output.write(block)
            temporary.replace(path)
        hashes[name] = file_hash(path)
        if name == "model.safetensors" and hashes[name] != WEIGHT_HASH:
            raise RuntimeError("Pinned target weight verification failed")
        print(json.dumps({"verified_file": name, "sha256": hashes[name]}), flush=True)
    (destination / "download_manifest.json").write_text(json.dumps({"model": MODEL,
        "revision": REVISION, "hashes": hashes}, indent=2), encoding="utf-8")
    return destination


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("destination")
    prepare(parser.parse_args().destination)
