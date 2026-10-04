"""Read-only account capability check; no jobs, files or endpoints are created."""
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from descend.controller.environment import load_controller_environment
from scripts.provider_preflight import NoRedirect


def main():
    load_controller_environment()
    key = os.environ["NEBIUS_API_KEY"]
    opener = urllib.request.build_opener(NoRedirect())
    result = {"timestamp": datetime.now(timezone.utc).isoformat(), "read_only": True, "paid_requests": 0, "checks": {}}
    for route in ("/v1/fine_tuning/jobs", "/v0/dedicated_endpoints"):
        request = urllib.request.Request("https://api.tokenfactory.nebius.com" + route,
                                         headers={"Authorization": "Bearer " + key})
        try:
            with opener.open(request, timeout=30) as response:
                payload = json.load(response)
            entries = payload.get("data", [])
            result["checks"][route] = {"http_status": 200, "object_count": len(entries),
                "response_fields": sorted(payload), "object_fields": sorted(entries[0]) if entries else []}
        except urllib.error.HTTPError as exc:
            result["checks"][route] = {"http_status": exc.code}
        except Exception as exc:
            result["checks"][route] = {"error_type": type(exc).__name__}
    Path("controller_state/training_access.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result))


if __name__ == "__main__":
    main()
