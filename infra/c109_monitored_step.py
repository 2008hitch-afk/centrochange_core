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
from c109_compose_gate import FINAL_PROJECT, DEMO_PROJECT, LIGHT_QA_PROJECT, IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT


class TestCommandFailed(RuntimeError):
    """A test assertion failed while every independent safety guard remained green."""


def main(root: Path, timeout: int, command: list[str], *, test_command: bool = False) -> None:
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    project = activation["target"]
    if project not in (FINAL_PROJECT, DEMO_PROJECT, LIGHT_QA_PROJECT, IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT) or not command or command[0] != "docker":
        raise RuntimeError("wrong isolated activation or command")
    if test_command and (command[:2] != ["docker", "exec"] or not any(
            arg.startswith(project + "-") for arg in command[2:])):
        raise RuntimeError("test mode requires docker exec on this activation only")
    now = dt.datetime.now(dt.timezone.utc)
    if not (dt.datetime.fromisoformat(activation["start_utc"]) <= now < dt.datetime.fromisoformat(activation["mutation_end_utc"])):
        raise RuntimeError("outside mutation window")
    initial_oom = oom_count()
    guard(state, initial_oom)
    with open(state / "bounded-step.log", "a") as log:
        process = subprocess.Popen(command, stdout=log, stderr=log)
        deadline = time.monotonic() + timeout
        try:
            while process.poll() is None:
                guard(state, initial_oom)
                if time.monotonic() >= deadline:
                    raise TimeoutError("bounded step deadline")
                time.sleep(0.25)
            guard(state, initial_oom)
            if process.returncode:
                if test_command:
                    with (state / "test-failures.jsonl").open("a") as stream:
                        stream.write(json.dumps({"time": dt.datetime.now(dt.timezone.utc).isoformat(),
                                                 "returncode": process.returncode,
                                                 "command_kind": "isolated docker exec"}) + "\n")
                    raise TestCommandFailed(f"isolated test exited {process.returncode}; guards remain active")
                raise RuntimeError(f"bounded Docker step exited {process.returncode}")
        except TestCommandFailed:
            # A failed assertion is evidence, not a safety event. The wrapper
            # already rechecked all guards; later tests may continue in-window.
            raise
        except BaseException:
            stop_only_ours(state, project)
            if process.poll() is None:
                process.terminate()
            raise


if __name__ == "__main__":
    if len(sys.argv) >= 6 and sys.argv[3:5] == ["--test", "--"]:
        main(Path(sys.argv[1]), int(sys.argv[2]), sys.argv[5:], test_command=True)
    elif len(sys.argv) >= 5 and sys.argv[3] == "--":
        main(Path(sys.argv[1]), int(sys.argv[2]), sys.argv[4:])
    else:
        raise SystemExit("usage: c109_monitored_step.py PRIVATE_ROOT TIMEOUT_SECONDS [--test] -- docker ...")
