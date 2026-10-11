"""Generate a C109-only Compose override for inert PID1 startup.

The override references existing *synthetic C109* volumes/networks as external;
it does not touch RC22. It contains no credentials and is written outside Git.
"""

import json
from pathlib import Path
import re
import sys

from c109_io_gate import READ_BPS, WRITE_BPS


KINDS = {
    "c-fit-backend": "frappe",
    "c-fit-frontend": "frappe",
    "c-fit-queue-long": "frappe",
    "c-fit-scheduler": "frappe",
    "c-fit-websocket": "frappe",
    "c-fit-db": "database",
    "c-fit-redis-cache": "redis",
    "c-fit-redis-queue": "redis",
}
PROJECT = "centrochange-c109-gated"
RETRY_PROJECT = "centrochange-c109-gated-r2"
FINAL_PROJECT = "centrochange-c109-gated-r3"
DEMO_PROJECT = "centrochange-c109-gated-r4"
LIGHT_QA_PROJECT = "centrochange-c109-gated-r5"
IO_CAPPED_PROJECT = "centrochange-c109-gated-r6"


def override(base: dict, gate_root: Path, script: Path, project: str = PROJECT,
             io_device: str | None = None) -> dict:
    if set(base["services"]) != set(KINDS):
        raise ValueError("unexpected C109 service inventory")
    if base.get("name") != "centrochange-c109":
        raise ValueError("wrong source Compose project")
    if project not in (PROJECT, RETRY_PROJECT, FINAL_PROJECT, DEMO_PROJECT, LIGHT_QA_PROJECT, IO_CAPPED_PROJECT):
        raise ValueError("unapproved isolated project")
    if project == IO_CAPPED_PROJECT and not (io_device and re.fullmatch(r"/dev/[A-Za-z0-9._-]+", io_device)):
        raise ValueError("I/O-capped project requires verified host block-device path")
    if project != IO_CAPPED_PROJECT and io_device is not None:
        raise ValueError("I/O device may only be specified for the dedicated capped project")
    if not script.is_file() or not gate_root.is_dir():
        raise ValueError("missing versioned bootstrap script or private gate root")
    result = {"name": project, "services": {}, "networks": {}, "volumes": {}}
    for name, kind in KINDS.items():
        if not (gate_root / name).is_dir():
            raise ValueError(f"missing gate directory: {name}")
        source = base["services"][name]
        if source.get("mem_limit") != source.get("memswap_limit"):
            raise ValueError(f"unexpected swap configuration: {name}")
        result["services"][name] = {
            "entrypoint": ["/bin/sh", "/opt/cc-bootstrap.sh", kind],
            "volumes": [
                {"type": "bind", "source": str(script.resolve()), "target": "/opt/cc-bootstrap.sh", "read_only": True},
                {"type": "bind", "source": str((gate_root / name).resolve()), "target": "/cc-bootstrap", "read_only": True},
            ],
        }
        if project == IO_CAPPED_PROJECT:
            result["services"][name]["blkio_config"] = {
                "device_read_bps": [{"path": io_device, "rate": READ_BPS}],
                "device_write_bps": [{"path": io_device, "rate": WRITE_BPS}],
            }
        # Compose drops the image CMD when replacing ENTRYPOINT. Restore the
        # immutable pinned image defaults where the base service has no CMD.
        # Without this Redis's entrypoint exits 0 and the backend never starts.
        if source.get("command") is None:
            if name == "c-fit-backend":
                result["services"][name]["command"] = ["start.sh"]
            elif kind == "redis":
                result["services"][name]["command"] = ["redis-server"]
            else:
                raise ValueError(f"missing original command: {name}")
    for kind in ("networks", "volumes"):
        for key, definition in base[kind].items():
            resource_name = definition.get("name")
            if not resource_name or not resource_name.startswith("centrochange-c109-"):
                raise ValueError(f"unexpected external resource: {kind}/{key}")
            result[kind][key] = {"external": True, "name": resource_name}
    return result


if __name__ == "__main__":
    if len(sys.argv) not in (5, 6, 7):
        raise SystemExit("usage: c109_compose_gate.py BASE_COMPOSE_JSON GATE_ROOT BOOTSTRAP_SH OUT_JSON [PROJECT [IO_DEVICE]]")
    base = json.loads(Path(sys.argv[1]).read_text())
    result = override(base, Path(sys.argv[2]), Path(sys.argv[3]),
                      sys.argv[5] if len(sys.argv) >= 6 else PROJECT,
                      sys.argv[6] if len(sys.argv) == 7 else None)
    output = Path(sys.argv[4])
    if output.exists():
        raise SystemExit("output already exists; no overwrite")
    output.write_text(json.dumps(result, indent=2) + "\n")
