"""Fail-closed Docker command scope for the isolated #139 restore rehearsal."""

import re


DEV_BACKEND = "centrochange-dev-backend-1"
CLONE_NAME = re.compile(r"cc139-restore-[0-9]{14}-bootstrap\Z")


class IsolationError(ValueError):
    pass


def scope_restore_command(args, clone):
    """Rewrite the executor's sole DEV target; reject all other Docker targets."""
    if not CLONE_NAME.fullmatch(clone) or len(args) < 3 or args[0] != "docker":
        raise IsolationError("invalid clone or Docker command")
    if args[1] not in ("exec", "cp"):
        raise IsolationError("Docker operation outside restore scope")
    scoped = []
    replacements = 0
    for arg in args:
        if arg == DEV_BACKEND:
            scoped.append(clone)
            replacements += 1
        elif arg.startswith(DEV_BACKEND + ":"):
            scoped.append(clone + arg[len(DEV_BACKEND):])
            replacements += 1
        else:
            scoped.append(arg)
    if replacements != 1 or any("centrochange-dev-" in str(arg) for arg in scoped):
        raise IsolationError("restore command could reach shared DEV")
    if args[1] == "cp":
        if len(scoped) != 4 or not str(scoped[-1]).startswith(
            clone + ":/home/frappe/frappe-bench/sites/centrochange.local/"
        ):
            raise IsolationError("restore copy must target clone Site")
    elif scoped.count(clone) != 1:
        raise IsolationError("restore exec must target one clone container")
    return scoped
