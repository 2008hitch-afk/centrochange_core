"""Write a full-ID protected Docker inventory for an isolated C109 activation.

The Docker event stream uses 64-character Actor.ID values. Short IDs would
silently disable exact comparison in protected-events.py.
"""

import json
from pathlib import Path
import re
import subprocess
import sys


def records(output: str) -> list[dict[str, str]]:
    ids = output.split()
    if not ids or len(ids) != len(set(ids)):
        raise ValueError("empty or duplicate Docker inventory")
    if any(not re.fullmatch(r"[0-9a-f]{64}", item) for item in ids):
        raise ValueError("Docker inventory must contain complete 64-character IDs")
    return [{"id": item} for item in ids]


def main(output: Path) -> None:
    if output.exists():
        raise ValueError("protected inventory already exists")
    raw = subprocess.check_output(["docker", "ps", "-aq", "--no-trunc"], text=True, timeout=15)
    output.write_text(json.dumps(records(raw), indent=2) + "\n")
    output.chmod(0o600)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: c109_protected_inventory.py PRIVATE_OUTPUT_JSON")
    main(Path(sys.argv[1]))
