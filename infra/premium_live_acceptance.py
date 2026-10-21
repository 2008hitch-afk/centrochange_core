#!/usr/bin/env python3
"""Run React live QA with a disposable, owned synthetic write fixture."""
import argparse
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time


ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend/premium"
SITE = "centrochange.local"


def private_file(value):
    path = Path(value).expanduser().resolve()
    if path == ROOT or ROOT in path.parents or not path.is_file() or path.stat().st_mode & 0o077:
        raise ValueError("Live fixture must be a private regular file outside Git")
    return path


def execute(container, method, kwargs=None):
    if container not in ("centrochange-dev-backend-1", "cc148-restore-runner"):
        raise ValueError("Unapproved acceptance backend")
    args = ["docker", "exec", container, "bench", "--site", SITE, "execute", method]
    if kwargs is not None:
        args.extend(("--kwargs", repr(kwargs)))
    result = subprocess.run(args, capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError("Private synthetic fixture operation failed: " + method)
    return json.loads(result.stdout)


def owned_write(fixture):
    tag = fixture.get("tag", "")
    catalog = fixture.get("catalog", {})
    centers = fixture.get("centers", [])
    items = catalog.get("Item", [])
    if (not re.fullmatch(r"CC-HTTP-[A-Za-z0-9]{10}", tag) or len(centers) != 2 or
            len(items) != 1 or items[0] != tag + " SESSION" or
            catalog.get("CC Public Booking Route") != []):
        raise ValueError("Synthetic write fixture is not uniquely owned or has a public route")
    return {"tag": tag, "center": centers[0], "item": items[0]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", required=True, help="Private read-only UAT session fixture")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--backend-container", default="centrochange-dev-backend-1")
    parser.add_argument("--base-url", default="http://127.0.0.1:8082")
    args = parser.parse_args()
    if not re.fullmatch(r"http://127\.0\.0\.1:\d+", args.base_url):
        raise ValueError("Acceptance URL must be loopback")
    source = private_file(args.fixture)
    base = json.loads(source.read_text())
    if base.get("synthetic_only") is not True or base.get("site") != SITE:
        raise ValueError("Synthetic single-Site fixture required")
    output = Path(args.output_dir).expanduser().resolve()
    if output == ROOT or ROOT in output.parents:
        raise ValueError("Acceptance evidence must remain outside Git")
    output.mkdir(mode=0o700, parents=True, exist_ok=True)
    os.chmod(output, 0o700)
    fixture = None
    test_status = None
    try:
        fixture = execute(args.backend_container,
            "centrochange_core.security.dev_acceptance.create_http",
            {"scheduling": True, "operations": False, "public_route": False})
        write = owned_write(fixture)
        with tempfile.TemporaryDirectory(prefix="cc148-live-owned-", dir=output) as temporary:
            path = Path(temporary) / "fixture.json"
            path.write_text(json.dumps({**base, "owned_write": write}))
            os.chmod(path, 0o600)
            env = {**os.environ, "CC_PREMIUM_LIVE_FIXTURE": str(path),
                   "CC_PREMIUM_LIVE_SYNTHETIC": "YES", "CC_PREMIUM_LIVE_URL": args.base_url}
            command = [str(FRONTEND / "node_modules/.bin/playwright"), "test",
                       "--config", "playwright.live.config.ts", "--reporter=line"]
            result = subprocess.run(command, cwd=FRONTEND, env=env, capture_output=True, text=True)
            log = output / "playwright.log"
            log.write_text(result.stdout + result.stderr)
            os.chmod(log, 0o600)
            test_status = result.returncode
    finally:
        if fixture is not None:
            users = [record["name"] for record in fixture["users"].values()]
            for _ in range(30):
                if execute(args.backend_container,
                    "centrochange_core.security.dev_acceptance.pending_contacts",
                    {"users": users})["pending"] == 0:
                    break
                time.sleep(1)
            else:
                raise RuntimeError("Owned fixture has pending native contact jobs")
            cleanup = execute(args.backend_container,
                "centrochange_core.security.dev_acceptance.recover_http",
                {"tag": fixture["tag"]})
            if cleanup.get("cleanup") != "PASS":
                raise RuntimeError("Owned fixture teardown failed")
    if test_status:
        raise RuntimeError("React live QA failed; inspect private playwright.log")
    print(json.dumps({"status": "PASS", "fixture_teardown": "PASS", "evidence": str(output)}))


if __name__ == "__main__":
    os.umask(0o077)
    main()
