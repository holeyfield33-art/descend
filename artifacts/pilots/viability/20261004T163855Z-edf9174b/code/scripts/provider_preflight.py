"""Read-only authenticated catalog check; never prints API credentials."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from descend.controller.environment import load_controller_environment
from descend.controller.token_factory import CONTROL_PLANE_BASE_URL


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def main():
    load_controller_environment()
    key = os.environ.get("NEBIUS_API_KEY", "").strip()
    if not key:
        raise SystemExit("Controller API key is missing")
    evidence = {"timestamp": datetime.now(timezone.utc).isoformat(),
                "operation": "read_only_catalog", "paid_requests": 0, "checks": {}}
    opener = urllib.request.build_opener(NoRedirect())
    output = Path("controller_state/provider_preflight.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    for path in ("/v1/models", "/v1/fine_tuning/models", "/v0/dedicated_endpoints/templates"):
        request = urllib.request.Request(CONTROL_PLANE_BASE_URL + path,
                                         headers={"Authorization": "Bearer " + key})
        try:
            with opener.open(request, timeout=30) as response:
                payload = json.load(response)
            evidence["checks"][path] = {"status": "ok", "response": payload}
            if path == "/v1/models":
                models = payload.get("data", [])
                print(json.dumps({"catalog_authenticated": True, "model_count": len(models),
                                  "nemotron_ids": [m["id"] for m in models if "nemotron" in m.get("id", "").lower()]}))
            else:
                print(json.dumps({"path": path, "status": "ok"}))
        except urllib.error.HTTPError as exc:
            evidence["checks"][path] = {"status": "http_error", "code": exc.code}
            print(json.dumps({"path": path, "status": "http_error", "code": exc.code}))
            if path == "/v1/models":
                output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
                raise SystemExit(1)
        except Exception as exc:
            evidence["checks"][path] = {"status": "connection_error", "type": type(exc).__name__}
            print(json.dumps({"path": path, "status": "connection_error", "type": type(exc).__name__}))
            if path == "/v1/models":
                output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")
                raise SystemExit(1)
    output.write_text(json.dumps(evidence, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
