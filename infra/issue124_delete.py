"""Single-use exact deletion for the explicitly approved issue #124 manifest."""

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess

from issue124_inventory import inventory


MANIFEST = pathlib.Path(__file__).resolve().parents[1] / "docs/evidence/issue-124/docker-delete-gate-2026-10-12.json"
APPROVED_SHA = "2a0e1e51c1ccaeff458b174a3d4711640ab741b07cd1baed3f7443ec4d4d4208"
STATE = pathlib.Path("/home/empv26/.local/state")


def run(*args):
    subprocess.run(args, check=True, stdout=subprocess.DEVNULL)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--execute", action="store_true", required=True)
    parser.add_argument("--approval-sha", required=True)
    args = parser.parse_args()
    if args.approval_sha != APPROVED_SHA:
        raise RuntimeError("Owner approval hash differs")
    if hashlib.sha256(MANIFEST.read_bytes()).hexdigest() != APPROVED_SHA:
        raise RuntimeError("Manifest hash differs")
    expected = json.loads(MANIFEST.read_text())
    if inventory() != expected:
        raise RuntimeError("Resource inventory drift; no deletion")
    deleted = expected["delete_after_owner_gate"]
    ids = {row["id"] for row in deleted["containers"]}
    names = {row["name"] for row in deleted["containers"]}
    if len(ids) != 241 or len(deleted["volumes"]) != 254 or len(deleted["networks"]) != 28 or len(deleted["state_paths"]) != 36:
        raise RuntimeError("Unexpected scope")
    if any(any(user not in names for user in row["users"]) for row in deleted["volumes"]):
        raise RuntimeError("Shared volume")
    if any(any(member not in ids for member in row["members"]) for row in deleted["networks"]):
        raise RuntimeError("Shared network")
    for path in deleted["state_paths"]:
        item = pathlib.Path(path)
        if item.parent != STATE or item.is_symlink() or not item.name.startswith("centrochange"):
            raise RuntimeError("Unsafe state path")
    print("GATE PASS: stopping only 9 approved RC22 containers", flush=True)
    running = [row["id"] for row in deleted["containers"] if row["state"] == "running"]
    run("docker", "stop", "--time", "20", *running)
    print("RC22 stopped; removing 241 approved containers", flush=True)
    run("docker", "rm", *sorted(ids))
    print("Removing 254 approved volumes", flush=True)
    run("docker", "volume", "rm", *(row["name"] for row in deleted["volumes"]))
    print("Removing 28 approved networks", flush=True)
    run("docker", "network", "rm", *(row["id"] for row in deleted["networks"]))
    print("Removing 36 approved demo state paths", flush=True)
    for path in deleted["state_paths"]:
        item = pathlib.Path(path)
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()
    print("EXACT DELETION COMPLETE", flush=True)


if __name__ == "__main__":
    main()
