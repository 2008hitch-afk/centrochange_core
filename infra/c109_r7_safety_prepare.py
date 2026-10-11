"""Prepare, never start, the private C109-r7 watchdog from the proven r6 file.

The I/O PSI sample remains in every record. Only IO_PSI is waived, for this
single activation, while an independent RC22 monitor becomes mandatory.
"""

from pathlib import Path
import hashlib
import json

from c109_compose_gate import IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT


def prepare(source: Path, destination: Path, activation: dict) -> str:
    if activation.get("target") not in (IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT) or activation.get("io_waiver") is not True or activation.get("issue") != 109:
        raise ValueError("not an authorized isolated I/O waiver")
    if destination.exists():
        raise ValueError("refusing to overwrite watchdog")
    raw = source.read_text()
    old = "if ip['full']>=1:errs.append('IO_PSI')"
    if raw.count(old) != 1 or raw.count("ip=psi('io')") != 1:
        raise ValueError("unexpected watchdog source")
    raw = raw.replace(old, "if (r/'rc22-alert.json').exists() or not (r/'rc22-heartbeat').exists() or time.time()-float((r/'rc22-heartbeat').read_text())>8:errs.append('RC22_INDEPENDENT_MONITOR')")
    if "if ip['full']>=1:errs.append('IO_PSI')" in raw or "'io_psi':ip" not in raw:
        raise ValueError("I/O waiver or telemetry invalid")
    for essential in ("'OOM'", "'MEMORY_RESERVE'", "'CAP_NOT_ENFORCED'",
                      "'DISK_RESERVE'", "'PROTECTED_EVENT_MONITOR'", "'UAT_HTTP'"):
        if essential not in raw:
            raise ValueError(f"essential guard absent: {essential}")
    destination.write_text(raw)
    return hashlib.sha256(raw.encode()).hexdigest()


if __name__ == "__main__":
    import sys
    if len(sys.argv) != 4:
        raise SystemExit("usage: c109_r7_safety_prepare.py R6_SAFETY R7_SAFETY ACTIVATION_JSON")
    print(prepare(Path(sys.argv[1]), Path(sys.argv[2]),
                  json.loads(Path(sys.argv[3]).read_text())))
