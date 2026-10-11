"""Stop only the isolated C109 visual demo at its authorized UTC deadline."""

import datetime as dt
import json
from pathlib import Path
import sys

from c109_compose_gate import DEMO_PROJECT
from c109_gated_start import stop_only_ours


def expire(root: Path) -> None:
    state = root / "app-run"
    activation = json.loads((state / "activation.json").read_text())
    if activation.get("target") != DEMO_PROJECT or activation.get("issue") != 109:
        raise RuntimeError("unexpected demo activation")
    deadline = dt.datetime.fromisoformat(activation["hard_stop_utc"])
    if dt.datetime.now(dt.timezone.utc) < deadline:
        raise RuntimeError("demo deadline has not arrived")
    stop_only_ours(state, DEMO_PROJECT)
    (state / "expired-utc").write_text(dt.datetime.now(dt.timezone.utc).isoformat())


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_demo_expiry.py PRIVATE_ACTIVATION_ROOT")
    expire(Path(sys.argv[1]))
