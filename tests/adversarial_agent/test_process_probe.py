"""Adversarial: process/proc inspection from agent subprocess."""

from __future__ import annotations

import tempfile
from pathlib import Path

from descend.sandbox.isolation import run_agent_script


def test_agent_proc_probe_runs_in_subprocess():
    """
    Agent script attempts to read /proc. This is not kernel-blocked in Phase 1.5
    (same UID). We verify the probe runs under cwd=workspace and records what
    it can see. Residual risk is documented in THREAT_MODEL.md.
    """
    with tempfile.TemporaryDirectory() as tmp:
        ws = Path(tmp) / "ws"
        ws.mkdir()
        script = ws / "probe_proc.py"
        script.write_text(
            "import os, json\n"
            "info = {\n"
            "  'cwd': os.getcwd(),\n"
            "  'proc_exists': os.path.isdir('/proc'),\n"
            "  'can_list_proc': False,\n"
            "  'cmdline_self': None,\n"
            "}\n"
            "try:\n"
            "  info['can_list_proc'] = len(os.listdir('/proc')) > 0\n"
            "except Exception as e:\n"
            "  info['proc_error'] = str(e)\n"
            "try:\n"
            "  with open('/proc/self/cmdline','rb') as f:\n"
            "    info['cmdline_self'] = f.read().decode('utf-8','replace')[:200]\n"
            "except Exception as e:\n"
            "  info['cmdline_error'] = str(e)\n"
            "print(json.dumps(info))\n",
            encoding="utf-8",
        )
        result = run_agent_script(script, ws, timeout_sec=10)
        assert result["returncode"] == 0, result
        import json
        data = json.loads(result["stdout"].strip().splitlines()[-1])
        # cwd must be the workspace
        assert data["cwd"] == str(ws.resolve()) or data["cwd"] == str(ws)
        # Document: /proc typically visible under same-UID isolation
        # This is a known residual escape route without containers.
        assert "proc_exists" in data
