"""Independent RC22 health guard for the single C109 I/O-waiver activation.

The only mutating action is stopping containers with the exact C109-r7
Compose label. RC22 is never restarted, stopped or inspected for secrets.
"""

import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time
import urllib.request

from c109_compose_gate import IO_WAIVER_PROJECT

PING = "http://127.0.0.1:8082/api/method/ping"
WEB = "http://127.0.0.1:8082/centrochange"
SLOW_SECONDS = 1.0
HARD_SECONDS = 3.0
INTERVAL_SECONDS = 2.0


def rc22_ids(run=subprocess.check_output):
    return sorted(run(["docker", "ps", "-q", "--no-trunc",
                       "--filter", "label=com.docker.compose.project=centrochange-dev"],
                      text=True, timeout=8).split())


def c109_ids(run=subprocess.check_output):
    return run(["docker", "ps", "-q", "--no-trunc",
                "--filter", f"label=com.docker.compose.project={IO_WAIVER_PROJECT}"],
               text=True, timeout=8).split()


def stop_c109(run=subprocess.run):
    ids = c109_ids()
    if ids:
        result = run(["docker", "stop", "--time", "10", *ids],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                     timeout=60, check=False)
        if result.returncode:
            raise RuntimeError("C109 targeted stop failed")


def probe(urlopen=urllib.request.urlopen):
    started = time.monotonic()
    try:
        for url in (PING, WEB):
            with urlopen(url, timeout=HARD_SECONDS) as response:
                code = response.status
                response.read(128)
                if code != 200:
                    break
    except Exception:
        return None, time.monotonic() - started
    return code, time.monotonic() - started


def verdict(expected, actual, code, latency, consecutive_slow):
    if actual != expected:
        return "RC22_CONTAINER_IDENTITY", consecutive_slow
    if code != 200:
        return "RC22_HTTP", consecutive_slow
    if latency >= HARD_SECONDS:
        return "RC22_HARD_LATENCY", consecutive_slow
    consecutive_slow = consecutive_slow + 1 if latency >= SLOW_SECONDS else 0
    if consecutive_slow >= 3:
        return "RC22_SUSTAINED_LATENCY", consecutive_slow
    return None, consecutive_slow


def require_rc22_monitor(state):
    heartbeat = state / "rc22-heartbeat"
    if (not heartbeat.exists() or time.time() - float(heartbeat.read_text()) > 8
            or (state / "rc22-alert.json").exists()):
        raise RuntimeError("independent RC22 monitor absent or alert")


def main(root):
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if (activation.get("issue"), activation.get("target"), activation.get("io_waiver")) != (109, IO_WAIVER_PROJECT, True):
        raise RuntimeError("wrong isolated activation")
    expected = json.loads((state / "rc22-before.json").read_text())["ids"]
    if len(expected) != 9 or rc22_ids() != expected:
        raise RuntimeError("RC22 baseline identity mismatch")
    slow = 0
    while not (state / "monitor-finish").exists():
        try:
            actual = rc22_ids()
            code, latency = probe()
            alert, slow = verdict(expected, actual, code, latency, slow)
        except Exception:
            alert, code, latency = "RC22_MONITOR_ERROR", None, None
        sample = {"time": dt.datetime.now(dt.timezone.utc).isoformat(),
                  "http": code, "latency_seconds": latency, "alert": alert}
        with (state / "rc22-health.jsonl").open("a") as stream:
            stream.write(json.dumps(sample) + "\n")
        (state / "rc22-heartbeat.tmp").write_text(str(time.time()))
        (state / "rc22-heartbeat.tmp").replace(state / "rc22-heartbeat")
        if alert:
            (state / "rc22-alert.json").write_text(json.dumps(sample))
            stop_c109()
            return 2
        time.sleep(INTERVAL_SECONDS)
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_rc22_monitor.py PRIVATE_ACTIVATION_ROOT")
    raise SystemExit(main(Path(sys.argv[1])))
