#!/usr/bin/env python3
"""CC-CAP-037 isolated upgrade/migration rehearsal helpers.

This helper is intentionally orchestration-light: it validates immutable target
inputs and produces normalized/hash evidence without embedding secrets or raw
backup contents in Git. Upgrade/restore commands remain explicit in README.md
and must target an isolated Compose project/site only.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import subprocess
import sys
from typing import Any

SHA40 = re.compile(r"^[0-9a-f]{40}$")
IMAGE_PIN = re.compile(r"^[^\s]+:[^\s]+@sha256:[0-9a-f]{64}$")
PLACEHOLDER = re.compile(r"REQUIRED|PLACEHOLDER|TODO", re.I)


def load_json(path: pathlib.Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError("top-level JSON object required")
    return data


def dump(data: Any) -> None:
    print(json.dumps(data, indent=2, sort_keys=True))


def cmd_validate_target(args: argparse.Namespace) -> int:
    data = load_json(pathlib.Path(args.manifest))
    errors: list[str] = []
    if data.get("capability_id") != "CC-CAP-037":
        errors.append("capability_id must be CC-CAP-037")

    isolated = data.get("isolated") or {}
    policy = data.get("policy") or {}
    project = isolated.get("compose_project", "")
    site = isolated.get("site", "")
    shared_project = policy.get("forbid_shared_project", "centrochange-dev")
    shared_site = policy.get("forbid_shared_site", "centrochange.local")
    shared_prefix = policy.get("forbid_shared_resource_prefix", "centrochange-dev-")

    for label, value in (("compose_project", project), ("site", site), ("workdir", isolated.get("workdir", ""))):
        if not isinstance(value, str) or not value or PLACEHOLDER.search(value):
            errors.append(f"isolated.{label} must be concrete and contain no placeholder")
    if project == shared_project or project.startswith(shared_prefix):
        errors.append("isolated compose project collides with shared runtime")
    if site == shared_site:
        errors.append("isolated site collides with shared runtime")

    target = data.get("target") or {}
    image = target.get("erpnext_image", "")
    if not isinstance(image, str) or not IMAGE_PIN.fullmatch(image) or PLACEHOLDER.search(image):
        errors.append("target.erpnext_image must be immutable tag@sha256:<64 hex>")

    for app in ("frappe", "erpnext", "builder", "healthcare", "centrochange_core"):
        commit = ((target.get(app) or {}).get("commit", ""))
        if not isinstance(commit, str) or not SHA40.fullmatch(commit):
            errors.append(f"target.{app}.commit must be exact 40-hex SHA")

    for app in ("frappe", "erpnext"):
        version = ((target.get(app) or {}).get("version", ""))
        if not isinstance(version, str) or not version or PLACEHOLDER.search(version):
            errors.append(f"target.{app}.version must be concrete")

    builder_tag = ((target.get("builder") or {}).get("tag", ""))
    if not isinstance(builder_tag, str) or not builder_tag or PLACEHOLDER.search(builder_tag):
        errors.append("target.builder.tag must be concrete")

    forbidden_true = {
        "allow_manual_sql_fix": False,
        "allow_container_source_edit": False,
        "allow_uncommitted_patch": False,
    }
    for key, expected in forbidden_true.items():
        if policy.get(key) is not expected:
            errors.append(f"policy.{key} must be {str(expected).lower()}")

    result = {
        "check": "validate-target",
        "ok": not errors,
        "errors": errors,
        "target_manifest_sha256": hashlib.sha256(pathlib.Path(args.manifest).read_bytes()).hexdigest(),
        "isolated": {"compose_project": project, "site": site, "workdir": isolated.get("workdir")},
    }
    dump(result)
    return 0 if not errors else 2


def cmd_assert_isolation(args: argparse.Namespace) -> int:
    values = [args.compose_project, args.site, *args.resources]
    errors = []
    if args.compose_project == "centrochange-dev" or args.compose_project.startswith("centrochange-dev-"):
        errors.append("compose project is shared or uses shared prefix")
    if args.site == "centrochange.local":
        errors.append("site is shared site")
    for resource in args.resources:
        if resource.startswith("centrochange-dev-"):
            errors.append(f"resource targets shared prefix: {resource}")
    dump({"check": "assert-isolation", "ok": not errors, "values": values, "errors": errors})
    return 0 if not errors else 2


def sha256_file(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def cmd_hash_checkpoint(args: argparse.Namespace) -> int:
    rows = []
    for raw in args.files:
        path = pathlib.Path(raw)
        if not path.is_file():
            dump({"check": "hash-checkpoint", "ok": False, "error": f"not a file: {path}"})
            return 2
        rows.append({"name": path.name, "size": path.stat().st_size, "sha256": sha256_file(path)})
    dump({"check": "hash-checkpoint", "ok": True, "files": rows})
    return 0


def git(args: list[str], cwd: pathlib.Path) -> str:
    cp = subprocess.run(["git", *args], cwd=cwd, check=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return cp.stdout.strip()


def cmd_git_clean(args: argparse.Namespace) -> int:
    rows = []
    ok = True
    for raw in args.paths:
        path = pathlib.Path(raw).resolve()
        try:
            status = git(["status", "--porcelain"], path)
            head = git(["rev-parse", "HEAD"], path)
            clean = status == ""
        except Exception as exc:  # noqa: BLE001
            rows.append({"path": str(path), "ok": False, "error": str(exc)})
            ok = False
            continue
        rows.append({"path": str(path), "ok": clean, "head": head, "dirty_entries": status.splitlines() if status else []})
        ok = ok and clean
    dump({"check": "git-clean", "ok": ok, "repositories": rows})
    return 0 if ok else 2


def normalize_inventory(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: normalize_inventory(obj[k]) for k in sorted(obj)}
    if isinstance(obj, list):
        normalized = [normalize_inventory(v) for v in obj]
        try:
            return sorted(normalized, key=lambda x: json.dumps(x, sort_keys=True))
        except TypeError:
            return normalized
    return obj


def cmd_compare_inventory(args: argparse.Namespace) -> int:
    before = normalize_inventory(load_json(pathlib.Path(args.before)))
    after = normalize_inventory(load_json(pathlib.Path(args.after)))
    same = before == after
    before_hash = hashlib.sha256(json.dumps(before, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    after_hash = hashlib.sha256(json.dumps(after, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    dump({"check": "compare-inventory", "ok": same, "before_sha256": before_hash, "after_sha256": after_hash})
    return 0 if same else 3


def cmd_target_differs(args: argparse.Namespace) -> int:
    current = load_json(pathlib.Path(args.current))
    manifest = load_json(pathlib.Path(args.manifest))
    target = manifest.get("target") or {}
    keys = ("frappe", "erpnext", "builder", "healthcare", "centrochange_core")
    diffs = {}
    for key in keys:
        cur = (current.get(key) or {}).get("commit")
        tgt = (target.get(key) or {}).get("commit")
        diffs[key] = {"current": cur, "target": tgt, "different": bool(cur and tgt and cur != tgt)}
    current_image = current.get("erpnext_image")
    target_image = target.get("erpnext_image")
    diffs["erpnext_image"] = {"current": current_image, "target": target_image, "different": bool(current_image and target_image and current_image != target_image)}
    any_diff = any(v["different"] for v in diffs.values())
    dump({"check": "target-differs", "ok": any_diff, "diffs": diffs})
    return 0 if any_diff else 2


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    sub = p.add_subparsers(dest="command", required=True)

    sp = sub.add_parser("validate-target")
    sp.add_argument("manifest")
    sp.set_defaults(func=cmd_validate_target)

    sp = sub.add_parser("assert-isolation")
    sp.add_argument("--compose-project", required=True)
    sp.add_argument("--site", required=True)
    sp.add_argument("resources", nargs="*")
    sp.set_defaults(func=cmd_assert_isolation)

    sp = sub.add_parser("hash-checkpoint")
    sp.add_argument("files", nargs="+")
    sp.set_defaults(func=cmd_hash_checkpoint)

    sp = sub.add_parser("git-clean")
    sp.add_argument("paths", nargs="+")
    sp.set_defaults(func=cmd_git_clean)

    sp = sub.add_parser("compare-inventory")
    sp.add_argument("before")
    sp.add_argument("after")
    sp.set_defaults(func=cmd_compare_inventory)

    sp = sub.add_parser("target-differs")
    sp.add_argument("current", help="sanitized current-pin JSON collected from isolated current clone")
    sp.add_argument("manifest")
    sp.set_defaults(func=cmd_target_differs)
    return p


def main() -> int:
    args = parser().parse_args()
    try:
        return args.func(args)
    except (OSError, ValueError, json.JSONDecodeError, subprocess.CalledProcessError) as exc:
        dump({"ok": False, "error": str(exc)})
        return 2


if __name__ == "__main__":
    sys.exit(main())
