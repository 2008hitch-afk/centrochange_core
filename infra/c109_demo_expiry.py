"""Stop only the isolated C109 visual demo at its authorized UTC deadline."""

import datetime as dt
import json
from pathlib import Path
import sys
import time

from c109_compose_gate import IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT, R14_PROJECT
from c109_guard_access import require_live_guards
from c109_gated_start import stop_only_ours


def expire(root: Path) -> None:
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if activation.get("target") not in (IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT, R14_PROJECT) or activation.get("issue") != 109:
        raise RuntimeError("unexpected demo activation")
    deadline = dt.datetime.fromisoformat(activation["hard_stop_utc"])
    if dt.datetime.now(dt.timezone.utc) < deadline:
        raise RuntimeError("demo deadline has not arrived")
    stop_only_ours(state, activation["target"])
    (state / "expired-utc").write_text(dt.datetime.now(dt.timezone.utc).isoformat())


if __name__ == "__main__":
    if len(sys.argv) == 3 and sys.argv[1] == "--wait":
        root = Path(sys.argv[2])
        activation = json.loads((root / "app-run" / "activation.json").read_text())
        if activation.get("target") not in (IO_CAPPED_PROJECT, IO_WAIVER_PROJECT, FINAL_UI_PROJECT, R9_PROJECT, R10_PROJECT, R11_PROJECT, R12_PROJECT, R13_PROJECT, R14_PROJECT) or activation.get("issue") != 109:
            raise RuntimeError("unexpected demo activation")
        deadline = dt.datetime.fromisoformat(activation["hard_stop_utc"])
        while not (root / "app-run" / "monitor-finish").exists():
            try:
                require_live_guards(root / "app-run")
            except (OSError, ValueError, KeyError, RuntimeError):
                (root / "app-run" / "expiry-guard-alert").write_text("GUARD_SCOPE_LOST\n")
                stop_only_ours(root / "app-run", activation["target"])
                raise RuntimeError("C109 guard scope lost; demo stopped")
            remaining = (deadline - dt.datetime.now(dt.timezone.utc)).total_seconds()
            if remaining <= 0:
                expire(root)
                break
            time.sleep(min(remaining, 2))
    elif len(sys.argv) == 2:
        expire(Path(sys.argv[1]))
    else:
        raise SystemExit("usage: c109_demo_expiry.py [--wait] PRIVATE_ACTIVATION_ROOT")
