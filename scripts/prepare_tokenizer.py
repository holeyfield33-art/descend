"""Download pinned tokenizer data only; no weights, tokens or remote code."""
import hashlib
import urllib.request
from pathlib import Path

REPOSITORY = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
REVISION = "bf77c3174f68ad409e1c2aa60daeb46e32d1c606"
TOKENIZER_HASH = "c6021eb6847e682f89aa52d5eb6e8c7d902a23acfc8137e25211cf84828f1592"
TOKENIZER_SOURCES = {
    "nano": {"repository": REPOSITORY, "revision": REVISION, "sha256": TOKENIZER_HASH,
             "path": "controller_state/nemotron-tokenizer.json"},
    "super": {"repository": "nvidia/NVIDIA-Nemotron-3-Super-120B-A12B-BF16",
              "revision": "2dc98e2afe4face0e4ce40972a915c45368bd34a",
              "sha256": "623c34567aebb18582765289fbe23d901c62704d6518d71866e0e58db892b5b7",
              "path": "controller_state/nemotron-super-tokenizer.json"},
}


def prepare(path=None, *, model="nano"):
    source = TOKENIZER_SOURCES[model]
    destination = Path(path or source["path"])
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == source["sha256"]:
        return destination
    url = f"https://huggingface.co/{source['repository']}/resolve/{source['revision']}/tokenizer.json"
    with urllib.request.urlopen(url, timeout=60) as response:
        content = response.read(25_000_001)
    if len(content) > 25_000_000 or hashlib.sha256(content).hexdigest() != source["sha256"]:
        raise RuntimeError("Pinned tokenizer verification failed")
    destination.write_bytes(content)
    return destination


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=TOKENIZER_SOURCES, default="nano")
    print(f"Verified tokenizer: {prepare(model=parser.parse_args().model)}")
