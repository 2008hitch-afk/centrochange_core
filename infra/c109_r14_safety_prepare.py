"""Install the exact versioned R14 watchdog into the private activation root."""

import hashlib
import json
import os
from pathlib import Path
import stat
import tempfile

from c109_compose_gate import R14_PROJECT


SOURCE = Path(__file__).with_name("c109_r14_safety.py")
EVENT_SOURCE = Path(__file__).with_name("c109_protected_events.py")


def install_private_safety(state):
    directory = state.stat()
    if directory.st_uid != os.getuid() or stat.S_IMODE(directory.st_mode) & 0o077:
        raise RuntimeError("R14 watchdog state directory is not private")
    activation = json.loads((state / "activation.json").read_text())
    if (activation.get("target") != R14_PROJECT or activation.get("issue") != 109
            or activation.get("io_waiver") is not True):
        raise RuntimeError("R14 private watchdog authorization mismatch")
    payload = SOURCE.read_bytes()
    target = state / "safety.py"
    if target.exists():
        info = target.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or target.read_bytes() != payload):
            raise RuntimeError("R14 private watchdog differs from verified source")
    else:
        fd, temporary = tempfile.mkstemp(prefix=".safety.", dir=state)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    if hashlib.sha256(target.read_bytes()).digest() != hashlib.sha256(payload).digest():
        raise RuntimeError("R14 private watchdog integrity mismatch")
    return hashlib.sha256(payload).hexdigest()


def install_private_events(state):
    directory = state.stat()
    if directory.st_uid != os.getuid() or stat.S_IMODE(directory.st_mode) & 0o077:
        raise RuntimeError("R14 event monitor state directory is not private")
    payload = EVENT_SOURCE.read_bytes()
    target = state / "protected-events.py"
    if target.exists():
        info = target.lstat()
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or target.read_bytes() != payload):
            raise RuntimeError("R14 event monitor differs from verified source")
    else:
        fd, temporary = tempfile.mkstemp(prefix=".events.", dir=state)
        try:
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, target)
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
    if target.read_bytes() != payload:
        raise RuntimeError("R14 event monitor integrity mismatch")
    return hashlib.sha256(payload).hexdigest()
