"""Replace only C109-r7 frontend with a verified versioned OCI image.

This is an in-window update, not another lab activation. The new frontend is
inert until its actual memory/swap cgroup is verified. Fail closed on any
guard event; never touch the nine protected RC22 containers.
"""

import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import sys
import time

from c109_cgroup_gate import read_snapshot
from c109_compose_gate import IO_WAIVER_PROJECT
from c109_gated_start import guard, inspect, oom_count, run, stop_only_ours

SERVICE = "c-fit-frontend"
LIMIT = 32 * 1024**2


def service_container_id(service: str, query=run) -> str:
    value = query("docker", "ps", "-aq", "--no-trunc",
                  "--filter", f"label=com.docker.compose.project={IO_WAIVER_PROJECT}",
                  "--filter", f"label=com.docker.compose.service={service}")
    if not re.fullmatch(r"[0-9a-f]{64}", value):
        raise RuntimeError("service container ID must be one exact full Docker ID")
    return value


def main(root: Path, image: str, expected_asset_hash: str):
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if (activation.get("target"), activation.get("io_waiver")) != (IO_WAIVER_PROJECT, True):
        raise RuntimeError("wrong activation")
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["mutation_end_utc"]):
        raise RuntimeError("window expired")
    if not (state / "app-bootstrap-green").exists() or (state / "frontend-update-attempted").exists():
        raise RuntimeError("bootstrap incomplete or update already attempted")
    if not image.startswith("sha256:") or len(image) != 71 or len(expected_asset_hash) != 64:
        raise RuntimeError("invalid immutable image or asset hash")
    if run("docker", "image", "inspect", "-f", "{{index .Config.Labels \"org.opencontainers.image.revision\"}}", image) != activation.get("frontend_revision"):
        raise RuntimeError("image revision differs from source activation")
    initial_oom = oom_count()
    guard(state, initial_oom)
    base = json.loads((state / "compose-final-private.json").read_text())
    prior = base["services"][SERVICE]["image"]
    if prior != activation["image_manifest"]:
        raise RuntimeError("unexpected original frontend image")
    base["services"][SERVICE]["image"] = image
    target = state / "compose-frontend-update-private.json"
    if target.exists():
        raise RuntimeError("update Compose already exists")
    target.write_text(json.dumps(base, indent=2))
    target.chmod(0o600)
    compose = ["docker", "compose", "--env-file", "/home/empv26/.local/state/centrochange-c109/runtime.env",
               "-f", str(target), "-f", str(root / "compose-gated.override.json"),
               "--project-name", IO_WAIVER_PROJECT]
    normalized = json.loads(subprocess.check_output(compose + ["config", "--format", "json"], text=True, timeout=15))
    current = json.loads((state / "compose-final.merged-private.json").read_text())
    assert normalized["services"][SERVICE]["image"] == image
    normalized["services"][SERVICE]["image"] = prior
    if normalized != current:
        raise RuntimeError("frontend update Compose changes more than image")
    (state / "frontend-update-attempted").write_text(dt.datetime.now(dt.timezone.utc).isoformat())
    gate = root / "gates" / SERVICE / "release"
    if not gate.is_file():
        raise RuntimeError("original frontend release gate missing")
    old = service_container_id(SERVICE)
    try:
        qa = run("docker", "ps", "-q", "--filter", "name=^centrochange-c109-gated-r7-qa$")
        if qa:
            subprocess.run(["docker", "stop", "--time", "10", qa], check=True, timeout=30,
                           stdout=subprocess.DEVNULL)
        guard(state, initial_oom)
        gate.unlink()
        with (state / "frontend-update.log").open("w") as log:
            subprocess.run(compose + ["up", "--no-start", "--no-deps", "--force-recreate",
                                      "--pull", "never", SERVICE],
                           stdout=log, stderr=log, check=True, timeout=90)
        new = service_container_id(SERVICE)
        if new == old:
            raise RuntimeError("frontend replacement identity invalid")
        row = inspect(new)
        if row["running"] or row["memory"] != LIMIT or row["swap"] != LIMIT:
            raise RuntimeError("frontend HostConfig memory/swap invalid")
        if run("docker", "inspect", "-f", "{{.Image}}", new) != run("docker", "image", "inspect", "-f", "{{.Id}}", image):
            raise RuntimeError("frontend did not use verified image")
        guard(state, initial_oom)
        run("docker", "start", new)
        deadline = time.monotonic() + 3
        first = None
        while time.monotonic() < deadline:
            guard(state, initial_oom)
            row = inspect(new)
            if not row["running"] or row["pid"] <= 0:
                raise RuntimeError("new frontend inert PID exited")
            snapshot = read_snapshot(row["pid"], new, LIMIT)
            if first is None:
                first = snapshot
                seen = time.monotonic()
            elif snapshot.inode != first.inode:
                raise RuntimeError("frontend cgroup inode changed")
            if time.monotonic() - seen >= 0.2:
                break
            time.sleep(0.02)
        else:
            raise RuntimeError("frontend cgroup did not stabilize")
        gate.write_text(new + "\n")
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            guard(state, initial_oom)
            if inspect(new)["running"]:
                try:
                    asset = run("docker", "exec", new, "sha256sum",
                                "/home/frappe/frappe-bench/sites/assets/centrochange_core/js/cc_desk_client.js").split()[0]
                    if asset == expected_asset_hash:
                        (state / "frontend-update-green.json").write_text(json.dumps({
                            "container": new, "image": image, "asset_sha256": asset,
                            "verified_utc": dt.datetime.now(dt.timezone.utc).isoformat()}, indent=2))
                        return
                except subprocess.CalledProcessError:
                    pass
            time.sleep(0.5)
        raise RuntimeError("new frontend asset not served from verified image")
    except BaseException:
        stop_only_ours(state, IO_WAIVER_PROJECT)
        raise


if __name__ == "__main__":
    if len(sys.argv) != 4:
        raise SystemExit("usage: c109_gated_frontend_update.py PRIVATE_ROOT IMAGE_SHA256 ASSET_SHA256")
    main(Path(sys.argv[1]), sys.argv[2], sys.argv[3])
