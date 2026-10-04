"""Adversarial: environment secret exposure and network attempts."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from descend.sandbox.isolation import scrub_env, FORBIDDEN_ENV_KEYS, run_agent_script, try_outbound_http


def test_scrub_env_removes_secrets():
    polluted = {
        "PATH": "/usr/bin",
        "HOME": "/tmp",
        "NEBIUS_API_KEY": "sk-secret-nebius",
        "HF_TOKEN": "hf_secret",
        "HUGGINGFACE_TOKEN": "hf2",
        "OPENAI_API_KEY": "sk-oai",
        "DESCEND_CONTROLLER_ROOT": "/secret/controller",
        "DESCEND_HIDDEN_SEED": "42",
        "MY_API_SECRET": "x",
        "LANG": "C",
    }
    clean = scrub_env(polluted)
    assert "NEBIUS_API_KEY" not in clean
    assert "HF_TOKEN" not in clean
    assert "HUGGINGFACE_TOKEN" not in clean
    assert "OPENAI_API_KEY" not in clean
    assert "DESCEND_CONTROLLER_ROOT" not in clean
    assert "DESCEND_HIDDEN_SEED" not in clean
    assert "MY_API_SECRET" not in clean
    assert clean.get("PATH") == "/usr/bin"
    assert clean.get("LANG") == "C"


def test_agent_subprocess_env_has_no_secrets():
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        ws.mkdir()
        script = ws / "probe_env.py"
        script.write_text(
            "import os, json\n"
            "keys = sorted(os.environ.keys())\n"
            "bad = [k for k in keys if any(x in k.upper() for x in "
            "['NEBIUS','HF_TOKEN','HUGGINGFACE','API_KEY','SECRET','TOKEN','PASSWORD'])]\n"
            "print(json.dumps({'bad': bad, 'has_controller': 'DESCEND_CONTROLLER_ROOT' in os.environ}))\n",
            encoding="utf-8",
        )
        # Inject secrets into parent env temporarily
        old = os.environ.get("NEBIUS_API_KEY")
        os.environ["NEBIUS_API_KEY"] = "should-not-leak"
        os.environ["HF_TOKEN"] = "should-not-leak"
        try:
            result = run_agent_script(script, ws, timeout_sec=10)
        finally:
            if old is None:
                os.environ.pop("NEBIUS_API_KEY", None)
            else:
                os.environ["NEBIUS_API_KEY"] = old
            os.environ.pop("HF_TOKEN", None)

        assert result["returncode"] == 0, result
        import json
        data = json.loads(result["stdout"].strip().splitlines()[-1])
        assert data["bad"] == [], f"secrets leaked: {data['bad']}"
        assert data["has_controller"] is False


def test_outbound_http_attempt_recorded():
    """Record whether direct outbound HTTP succeeds from this process.
    Phase 1.5 does not claim kernel network namespace isolation.
    """
    result = try_outbound_http("http://127.0.0.1:9", timeout=0.5)
    assert result["attempted"] is True
    # Connection to closed port should fail (blocked/error)
    assert result["blocked"] is True or result["error"] is not None
