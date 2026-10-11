"""Run one bounded C109-only Docker step under the existing host safety gate.

The command must label every created container with the activation project.
At a guard trip, stop only that project, end the activation, and do not retry.
"""

import datetime as dt
import json
from pathlib import Path
import subprocess
import sys
import time

from c109_gated_start import guard, oom_count, run, stop_only_ours


def main(root: Path, timeout: int, command: list[str]) -> None:
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    project = activation["target"]
    if project != "centrochange-c109-gated-r3" or not command or command[0] != "docker":
        raise RuntimeError("wrong isolated activation or command")
    now = dt.datetime.now(dt.timezone.utc)
    if not (dt.datetime.fromisoformat(activation["start_utc"]) <= now < dt.datetime.fromisoformat(activation["mutation_end_utc"])):
        raise RuntimeError("outside mutation window")
    rc22 = sorted(run("docker", "ps", "-q", "--filter", "label=com.docker.compose.project=centrochange-dev").split())
    if len(rc22) != 9:
        raise RuntimeError("RC22 identity count changed")
    initial_oom = oom_count()
    guard(state, rc22, initial_oom)
    with open(state / "bounded-step.log", "a") as log:
        process = subprocess.Popen(command, stdout=log, stderr=log)
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                guard(state, rc22, initial_oom)
                if time.monotonic() >= deadline:
                    raise TimeoutError("bounded step deadline")
                time.sleep(0.25)
            guard(state, rc22, initial_oom)
            if process.returncode:
                raise RuntimeError(f"bounded Docker step exited {process.returncode}")
        except BaseException:
            stop_only_ours(state, project)
            if process.poll() is None:
                process.terminate()
            raise


if __name__ == "__main__":
    if len(sys.argv) < 5 or sys.argv[3] != "--":
        raise SystemExit("usage: c109_monitored_step.py PRIVATE_ROOT TIMEOUT_SECONDS -- docker ...")
    main(Path(sys.argv[1]), int(sys.argv[2]), sys.argv[4:])
