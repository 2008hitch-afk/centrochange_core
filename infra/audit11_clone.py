"""Ephemeral GitHub Actions runner ONLY; no contact with client DEV/STAGING."""
import json
import os
from pathlib import Path
import test_audit09_isolated_clone as clone

root = Path(__file__).resolve().parent.parent
if os.environ.get("GITHUB_ACTIONS") != "true" or not os.environ.get("RUNNER_TEMP"):
    raise RuntimeError("AUDIT-11 isolated clone may run only on ephemeral GitHub Actions")
if os.environ.get("CC_CLONE_IMAGE") != "cc201-audit11-ci:local":
    raise RuntimeError("AUDIT-11 CI must run the locally built pinned candidate, not a legacy image")

try:
    clone.setup_clone()
    backend = (root / "infra/audit11_clone_backend.py").read_text(encoding="utf-8")
    output = clone.run_cmd(
        ["docker", "exec", "-i", "-e", "FRAPPE_STREAM_LOGGING=1",
         "-w", "/home/frappe/frappe-bench", clone.BACKEND_CONTAINER,
         "env/bin/python", "-"],
        input_str=backend,
    )
    lines = [json.loads(line) for line in output.splitlines()
             if line.startswith("{") and '"status"' in line]
    assert len(lines) == 1 and lines[0].get("status") == "PASS", "No verified Frappe result"
    assert lines[0]["count"] == 4
    print("AUDIT11_NATIVE_FRAPPE_ISOLATED_PASS", json.dumps(lines[0]), flush=True)
finally:
    clone.cleanup()
