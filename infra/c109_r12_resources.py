"""Guarded, single-use preparation of the isolated R12 synthetic resources.

Only the R10 *copies* are sources.  The five original volumes and R10 copies
are never mounted writable.  This module is called by the verified R12 entry
point after all four guards start and before application containers exist.
"""

import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import time

from c109_cgroup_gate import read_snapshot
from c109_compose_gate import R12_PROJECT
from c109_gated_start import guard, oom_count


MEMORY = 256 * 1024**2
SOURCE_PREFIX = "centrochange-c109-r10-c-fit-"
DEST_PREFIX = "centrochange-c109-r12-c-fit-"
SUFFIXES = ("db-data", "redis-cache-data", "redis-queue-data", "sites", "assets")
NETWORKS = (("centrochange-c109-r12-c-fit-net", True),
            ("centrochange-c109-r12-c-fit-http", False))
ID = re.compile(r"[0-9a-f]{64}\Z")
SHA = re.compile(r"[0-9a-f]{64}\Z")

# This script hashes contents and names, types, modes and link targets without
# following links.  It prints only a digest, never patient or site file names.
TREE_DIGEST = r'''
import hashlib, os, stat, sys
h = hashlib.sha256()
def visit(path, relative):
    st = os.lstat(path)
    kind = stat.S_IFMT(st.st_mode)
    if kind not in (stat.S_IFDIR, stat.S_IFREG, stat.S_IFLNK):
        raise RuntimeError("unsupported volume file type")
    h.update(os.fsencode(relative) + b"\0" + str(kind).encode() + b"\0")
    h.update(str(stat.S_IMODE(st.st_mode)).encode() + b"\0")
    if stat.S_ISLNK(st.st_mode):
        h.update(os.fsencode(os.readlink(path)) + b"\0")
    elif stat.S_ISREG(st.st_mode):
        with open(path, "rb") as stream:
            while True:
                block = stream.read(65536)
                if not block: break
                h.update(block)
    else:
        with os.scandir(path) as scan:
            children = sorted(scan, key=lambda item: os.fsencode(item.name))
        for item in children:
            visit(item.path, relative + "/" + item.name)
visit(sys.argv[1], ".")
print(h.hexdigest())
'''


class Host:
    def run(self, *args, timeout=30):
        return subprocess.check_output(args, text=True, timeout=timeout,
                                       stderr=subprocess.DEVNULL).strip()

    def process(self, args):
        return subprocess.Popen(args, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.DEVNULL)

    def sleep(self, seconds):
        time.sleep(seconds)

    def snapshot(self, pid, container_id):
        return read_snapshot(pid, container_id, MEMORY)

    def safety(self, state, initial_oom):
        guard(state, initial_oom)


def _check(host, state, activation, initial_oom):
    if dt.datetime.now(dt.timezone.utc) >= dt.datetime.fromisoformat(activation["mutation_end_utc"]):
        raise RuntimeError("R12 resource preparation window expired")
    host.safety(state, initial_oom)


def _monitored(host, command, check, timeout=3600):
    check()
    process = host.process(command)
    end = time.monotonic() + timeout
    try:
        while process.poll() is None:
            check()
            if time.monotonic() >= end:
                raise RuntimeError("R12 volume operation deadline")
            host.sleep(0.25)
        check()
        if process.returncode:
            raise RuntimeError("R12 volume operation failed")
        output = process.communicate(timeout=1)[0].strip()
        return output
    except BaseException:
        if process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
        raise


def _inspect(host, kind, name):
    rows = json.loads(host.run("docker", kind, "inspect", name))
    if len(rows) != 1 or rows[0].get("Name") != name:
        raise RuntimeError(f"R12 {kind} identity mismatch")
    return rows[0]


def _helper_verified(host, container_id, source, dest):
    rows = json.loads(host.run("docker", "inspect", container_id))
    if len(rows) != 1:
        raise RuntimeError("R12 copy helper inspect ambiguous")
    item = rows[0]
    config = item["HostConfig"]
    mounts = item["Mounts"]
    if (item["Id"] != container_id or not item["State"]["Running"]
            or item["State"]["Pid"] <= 0 or config["Memory"] != MEMORY
            or config["MemorySwap"] != MEMORY or config["NetworkMode"] != "none"
            or item["Config"].get("User") != "0:0"
            or item["Config"]["Labels"].get("com.docker.compose.project") != R12_PROJECT
            or item["Config"]["Labels"].get("centrochange.mission") != "C109"
            or len(mounts) != 4):
        raise RuntimeError("R12 copy helper identity or cap mismatch")
    expected = {("/source", source, False), ("/dest", dest, True)}
    actual = {(m.get("Destination"), m.get("Name"), m.get("RW")) for m in mounts
              if m.get("Type") == "volume"}
    if actual != expected:
        raise RuntimeError("R12 copy helper mounts are not isolated/read-only")
    tmpfs = {m.get("Destination") for m in mounts if m.get("Type") == "tmpfs"
             and m.get("RW") is True}
    if tmpfs != {"/home/frappe/frappe-bench/logs", "/home/frappe/frappe-bench/sites"}:
        raise RuntimeError("R12 copy helper implicit image volumes not isolated")
    snap = host.snapshot(item["State"]["Pid"], container_id)
    if snap.memory_current > MEMORY:
        raise RuntimeError("R12 copy helper memory cap exceeded")
    return snap


def _copy_one(host, state, activation, initial_oom, source, dest, image):
    check = lambda: _check(host, state, activation, initial_oom)
    helper = None
    try:
        check()
        helper = host.run("docker", "create", "--label", f"com.docker.compose.project={R12_PROJECT}",
                          "--label", "centrochange.mission=C109",
                          "--network", "none", "--memory", str(MEMORY),
                          "--memory-swap", str(MEMORY), "--user", "0:0",
                          "--mount", f"type=volume,source={source},target=/source,readonly",
                          "--mount", f"type=volume,source={dest},target=/dest",
                          "--mount", "type=tmpfs,target=/home/frappe/frappe-bench/logs,tmpfs-size=1048576",
                          "--mount", "type=tmpfs,target=/home/frappe/frappe-bench/sites,tmpfs-size=1048576",
                          "--entrypoint", "/bin/sh", image,
                          "-c", "while :; do sleep 1; done")
        if not ID.fullmatch(helper):
            raise RuntimeError("R12 copy helper returned malformed ID")
        host.run("docker", "start", helper)
        first = _helper_verified(host, helper, source, dest)
        host.sleep(0.2)
        check()
        second = _helper_verified(host, helper, source, dest)
        if (first.pid, first.inode) != (second.pid, second.inode):
            raise RuntimeError("R12 copy helper cgroup changed before release")

        def live():
            check()
            users = set(host.run("docker", "ps", "-q", "--no-trunc", "--filter", f"volume={source}").split())
            if users != {helper}:
                raise RuntimeError("R10 source became active during clone")
            current = _helper_verified(host, helper, source, dest)
            if (current.pid, current.inode) != (first.pid, first.inode):
                raise RuntimeError("R12 copy helper cgroup changed")

        source_digest = _monitored(host, ["docker", "exec", helper, "python3", "-c", TREE_DIGEST, "/source"], live)
        if not SHA.fullmatch(source_digest):
            raise RuntimeError("R12 source digest malformed")
        _monitored(host, ["docker", "exec", helper, "cp", "-a", "/source/.", "/dest/"], live)
        dest_digest = _monitored(host, ["docker", "exec", helper, "python3", "-c", TREE_DIGEST, "/dest"], live)
        if dest_digest != source_digest:
            raise RuntimeError("R12 cloned volume integrity mismatch")
        if _monitored(host, ["docker", "exec", helper, "python3", "-c", TREE_DIGEST, "/source"], live) != source_digest:
            raise RuntimeError("R10 source changed during clone")
        live()
        return source_digest
    finally:
        if helper and ID.fullmatch(helper):
            # Remove only this disposable, labeled helper.  The copied volume is
            # retained on failure for investigation; no implicit retry occurs.
            try:
                host.run("docker", "stop", "--time", "10", helper, timeout=30)
            finally:
                host.run("docker", "rm", helper, timeout=30)


def prepare(root, *, host=None, image):
    """Prepare R12 once, guarded throughout; return private sanitized digest data."""
    host = host or Host()
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    config = json.loads((state / "compose-final.merged-private.json").read_text())
    if activation.get("target") != R12_PROJECT or config.get("name") != R12_PROJECT:
        raise RuntimeError("R12 project mismatch")
    if {v.get("name") for v in config.get("volumes", {}).values()} != {
            DEST_PREFIX + suffix for suffix in SUFFIXES}:
        raise RuntimeError("R12 volume mapping mismatch")
    if {n.get("name") for n in config.get("networks", {}).values()} != {n for n, _ in NETWORKS}:
        raise RuntimeError("R12 network mapping mismatch")
    if (state / "r12-resources-attempted").exists():
        raise RuntimeError("R12 resource preparation already attempted")
    initial_oom = oom_count()
    check = lambda: _check(host, state, activation, initial_oom)
    check()
    volumes = set(host.run("docker", "volume", "ls", "-q").split())
    networks = set(host.run("docker", "network", "ls", "--format", "{{.Name}}").split())
    if any(DEST_PREFIX + suffix in volumes for suffix in SUFFIXES) or any(name in networks for name, _ in NETWORKS):
        raise RuntimeError("R12 destination resources already exist")
    if any(SOURCE_PREFIX + suffix not in volumes for suffix in SUFFIXES):
        raise RuntimeError("R10 synthetic source volume missing")
    for suffix in SUFFIXES:
        source = SOURCE_PREFIX + suffix
        info = _inspect(host, "volume", source)
        if info.get("Driver") != "local" or info.get("Labels", {}).get("centrochange.mission") != "C109":
            raise RuntimeError("R10 source volume provenance invalid")
        if host.run("docker", "ps", "-q", "--filter", f"volume={source}"):
            raise RuntimeError("R10 source volume is mounted by a running container")
    if host.run("docker", "ps", "-aq", "--filter", f"label=com.docker.compose.project={R12_PROJECT}"):
        raise RuntimeError("R12 container already exists")
    if host.run("docker", "ps", "-q", "--filter", "label=centrochange.mission=C109"):
        raise RuntimeError("another C109 workload running")
    # The marker is created only after all read-only prerequisites, before the
    # first mutation. A partial clone must never be reused automatically.
    (state / "r12-resources-attempted").write_text(dt.datetime.now(dt.timezone.utc).isoformat())
    for name, internal in NETWORKS:
        check()
        cmd = ["docker", "network", "create", "--driver", "bridge", "--label",
               f"com.docker.compose.project={R12_PROJECT}"]
        if internal:
            cmd.append("--internal")
        host.run(*(cmd + [name]))
        network = _inspect(host, "network", name)
        if (network.get("Driver") != "bridge" or network.get("Internal") is not internal
                or network.get("Labels", {}).get("com.docker.compose.project") != R12_PROJECT
                or network.get("Containers")):
            raise RuntimeError("R12 network isolation mismatch")
    records = []
    for suffix in SUFFIXES:
        check()
        source, dest = SOURCE_PREFIX + suffix, DEST_PREFIX + suffix
        source_info = _inspect(host, "volume", source)
        if source_info.get("Driver") != "local":
            raise RuntimeError("R10 source volume driver changed")
        host.run("docker", "volume", "create", "--label", f"com.docker.compose.project={R12_PROJECT}", dest)
        dest_info = _inspect(host, "volume", dest)
        if (dest_info.get("Driver") != "local" or dest_info.get("Mountpoint") == source_info.get("Mountpoint")
                or dest_info.get("Labels", {}).get("com.docker.compose.project") != R12_PROJECT):
            raise RuntimeError("R12 volume isolation mismatch")
        digest = _copy_one(host, state, activation, initial_oom, source, dest, image)
        records.append({"source": source, "destination": dest, "sha256_tree": digest})
    check()
    (state / "r12-resource-integrity.json").write_text(json.dumps(records, indent=2) + "\n")
    return records
