"""Canonical, unambiguous RC22 container identity for every C109 guard."""

import json
import re


LABEL = "label=com.docker.compose.project=centrochange-dev"


def full_ids(raw):
    ids = raw.split() if isinstance(raw, str) else raw
    if (not isinstance(ids, list) or len(ids) != 9
            or any(not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{64}", item) for item in ids)
            or len(set(ids)) != 9):
        raise RuntimeError("RC22 requires nine distinct complete Docker IDs")
    return sorted(ids)


def baseline(state):
    data = json.loads((state / "rc22-before.json").read_text())
    if not isinstance(data, dict) or set(data) != {"ids"}:
        raise RuntimeError("RC22 baseline format changed")
    return full_ids(data["ids"])


def current(run):
    return full_ids(run("docker", "ps", "-q", "--no-trunc", "--filter", LABEL))


def verify(state, run):
    expected = baseline(state)
    if current(run) != expected:
        raise RuntimeError("RC22 container identity changed")
    return expected
