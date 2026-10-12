"""Offline attribution aid for C109 telemetry; no Docker or runtime access.

Host PSI is a stop signal, not proof that a sampled container caused it.
Use cgroup io.stat deltas and local PSI only as supporting observations.
"""

import json
from pathlib import Path
import re
import sys


def io_bytes(value, field):
    return sum(int(number) for number in re.findall(r"\b" + field + r"=(\d+)", value or ""))


def local_full(value):
    match = re.search(r"\bfull avg10=([0-9.]+)", value or "")
    return float(match.group(1)) if match else None


def analyze(samples, threshold=1.0):
    if len(samples) < 2:
        raise ValueError("at least two telemetry samples required")
    peaks = []
    for index, sample in enumerate(samples):
        host_full = float(sample["io_psi"]["full"])
        if host_full < threshold:
            continue
        prior = samples[index - 1] if index else None
        before = {p["name"]: p for p in prior["probes"]} if prior else {}
        observed = []
        for probe in sample["probes"]:
            previous = before.get(probe["name"])
            match = re.search(r"c-fit-(.+)-1$", probe["name"])
            observed.append({
                "service": match.group(1) if match else "qa",
                "read_delta": max(0, io_bytes(probe.get("io_stat"), "rbytes") - io_bytes(previous.get("io_stat"), "rbytes")) if previous else None,
                "write_delta": max(0, io_bytes(probe.get("io_stat"), "wbytes") - io_bytes(previous.get("io_stat"), "wbytes")) if previous else None,
                "local_full": local_full(probe.get("local_io_psi")),
            })
        peaks.append({"time": sample["time"], "host_full": host_full,
                      "host_memory_full": float(sample["psi"]["full"]),
                      "memory_available": int(sample["available"]),
                      "oom": int(sample["oom"]), "observed": observed})
    return {"sample_count": len(samples), "threshold": threshold, "crossings": peaks,
            "attribution": "UNPROVEN: host PSI includes work outside sampled C109 cgroups"}


def main(path):
    samples = [json.loads(line) for line in Path(path).read_text().splitlines() if line]
    print(json.dumps(analyze(samples), indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_io_analysis.py PRIVATE_MEMORY_SAMPLES_JSONL")
    main(sys.argv[1])
