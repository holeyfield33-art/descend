"""Download pinned tokenizer data only; no weights, tokens or remote code."""
import hashlib
import urllib.request
from pathlib import Path

REPOSITORY = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B-BF16"
REVISION = "bf77c3174f68ad409e1c2aa60daeb46e32d1c606"
TOKENIZER_HASH = "c6021eb6847e682f89aa52d5eb6e8c7d902a23acfc8137e25211cf84828f1592"


def prepare(path="controller_state/nemotron-tokenizer.json"):
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and hashlib.sha256(destination.read_bytes()).hexdigest() == TOKENIZER_HASH:
        return destination
    url = f"https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/tokenizer.json"
    with urllib.request.urlopen(url, timeout=60) as response:
        content = response.read(25_000_001)
    if len(content) > 25_000_000 or hashlib.sha256(content).hexdigest() != TOKENIZER_HASH:
        raise RuntimeError("Pinned tokenizer verification failed")
    destination.write_bytes(content)
    return destination


if __name__ == "__main__":
    print(f"Verified tokenizer: {prepare()}")
