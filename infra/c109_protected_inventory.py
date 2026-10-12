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


def validate_existing(content: str, current_ids: str) -> None:
    """Fail closed before using the private Docker event monitor."""
    saved = json.loads(content)
    if not isinstance(saved, list) or any(set(item) != {"id"} for item in saved if isinstance(item, dict)):
        raise ValueError("invalid protected inventory shape")
    if any(not isinstance(item, dict) for item in saved):
        raise ValueError("invalid protected inventory record")
    expected = {item["id"] for item in records(current_ids)}
    if len(saved) != len(expected) or {item["id"] for item in saved} != expected:
        raise ValueError("protected inventory differs from complete current Docker IDs")


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
