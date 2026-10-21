#!/usr/bin/env python3
"""Fail-closed, offline-verifiable snapshot of the complete Frappe sites volume.

The manifest belongs *inside* the encrypted checkpoint. Never print its paths or
file contents in command output: private/files and private/uat are sensitive.
"""
import hashlib
import gzip
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import stat
import tarfile
import tempfile


ASSET_LINK = "/home/frappe/frappe-bench/assets"  # pinned image build output
REQUIRED = {
    "sites/apps.json", "sites/apps.txt", "sites/common_site_config.json",
    "sites/centrochange.local/site_config.json",
    "sites/centrochange.local/private/uat/demo.json",
    "sites/centrochange.local/builder_analytics.duckdb",
    "sites/centrochange.local/touched_tables.json",
}


def _digest(stream):
    result = hashlib.sha256()
    for block in iter(lambda: stream.read(1024 * 1024), b""):
        result.update(block)
    return result.hexdigest()


def _name(name):
    stripped = name.rstrip("/")
    parts = stripped.split("/")
    if (not stripped or stripped.startswith("/") or "\\" in stripped or
            any(part in ("", ".", "..") for part in parts) or
            any(ord(c) < 32 for c in stripped) or parts[0] != "sites"):
        raise ValueError("Unsafe checkpoint member path")
    return stripped


def _link(name, target):
    if name != "sites/assets" or target != ASSET_LINK:
        raise ValueError("Unapproved checkpoint symlink")


def validate_native_archive(archive):
    """Reject unsafe members before giving Frappe's file tarballs to restore."""
    seen = set()
    with tarfile.open(archive, "r:*") as source:
        for member in source:
            name = member.name.removeprefix("./").rstrip("/")
            if name == "" and member.isdir():
                continue
            parts = name.split("/")
            if (not name or member.name.startswith("/") or "\\" in name or
                    any(part in ("", ".", "..") for part in parts) or
                    any(ord(c) < 32 for c in name) or name in seen):
                raise ValueError("Unsafe native file archive path")
            if not (member.isdir() or member.isfile()):
                raise ValueError("Native file archive contains a link or special file")
            seen.add(name)


def tar_manifest(archive):
    """Inspect every tar member, including empty dirs and zero-byte files."""
    entries = {}
    with tarfile.open(archive, "r:") as source:
        for member in source:
            name = _name(member.name)
            if name in entries:
                raise ValueError("Duplicate checkpoint member")
            if member.isdir():
                kind = "dir"
            elif member.isfile():
                kind = "file"
            elif member.issym():
                kind = "link"
                _link(name, member.linkname)
            else:
                raise ValueError("Special file or hardlink in checkpoint")
            if name != "sites":
                parent = str(PurePosixPath(name).parent)
                if parent not in entries or entries[parent]["kind"] != "dir":
                    raise ValueError("Missing or unsafe checkpoint parent")
            entry = {"kind": kind, "mode": member.mode & 0o777,
                     "uid": member.uid, "gid": member.gid}
            if kind == "file":
                data = source.extractfile(member)
                if data is None:
                    raise ValueError("Unreadable checkpoint member")
                entry.update(size=member.size, sha256=_digest(data))
            elif kind == "link":
                entry["target"] = member.linkname
            entries[name] = entry
    if entries.get("sites", {}).get("kind") != "dir":
        raise ValueError("Missing sites root")
    if any(entries.get(name, {}).get("kind") != "file" for name in REQUIRED):
        raise ValueError("Missing required Site state, including private UAT manifest")
    return {"format": 1, "entries": entries}


def tree_manifest(root):
    """Inventory a restored tree without following any symlink."""
    root = Path(root)
    entries = {}
    def visit(path, name):
        item = path.lstat()
        entry = {"mode": stat.S_IMODE(item.st_mode), "uid": item.st_uid,
                 "gid": item.st_gid}
        if stat.S_ISDIR(item.st_mode):
            entry["kind"] = "dir"
            entries[name] = entry
            for child in sorted(path.iterdir()):
                visit(child, name + "/" + child.name)
        elif stat.S_ISREG(item.st_mode):
            entry.update(kind="file", size=item.st_size)
            with path.open("rb") as data:
                entry["sha256"] = _digest(data)
            entries[name] = entry
        elif stat.S_ISLNK(item.st_mode):
            target = os.readlink(path)
            _link(name, target)
            entry.update(kind="link", target=target)
            entries[name] = entry
        else:
            raise ValueError("Special file in Site tree")
    visit(root, "sites")
    if any(entries.get(name, {}).get("kind") != "file" for name in REQUIRED):
        raise ValueError("Missing required Site state, including private UAT manifest")
    return {"format": 1, "entries": entries}


def compare(expected, actual, *, volatile_logs=False):
    """Compare exact names and metadata. Runtime logs may append after restore."""
    if expected.get("format") != 1 or actual.get("format") != 1:
        raise ValueError("Unsupported checkpoint manifest")
    left, right = expected["entries"], actual["entries"]
    names = set(left) | set(right)
    if volatile_logs:
        names = {name for name in names if "/logs/" not in name}
    for name in sorted(names):
        if left.get(name) != right.get(name):
            raise ValueError("Site restore differs from original checkpoint")
    return {"entries_checked": len(names), "files_checked": sum(left[n]["kind"] == "file" for n in names)}


def extract_verified(archive, manifest, destination):
    """Extract into an empty isolated *sites volume root*, preserving ownership."""
    destination = Path(destination)
    if any(parent.is_symlink() for parent in (destination, *destination.parents)):
        raise ValueError("Restore destination has a symlink parent")
    if destination.is_symlink() or (destination.exists() and any(destination.iterdir())):
        raise ValueError("Restore destination must be empty and non-symlink")
    compare(manifest, tar_manifest(archive))
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    directories = []
    links = []
    with tarfile.open(archive, "r:") as source:
        for member in source:
            name = _name(member.name)
            target = destination.joinpath(*PurePosixPath(name).parts[1:])
            entry = manifest["entries"][name]
            if entry["kind"] == "dir":
                target.mkdir(mode=0o700, exist_ok=name == "sites")
                directories.append((target, entry))
            elif entry["kind"] == "link":
                links.append((target, entry))
            else:
                data = source.extractfile(member)
                if data is None:
                    raise ValueError("Unreadable checkpoint member")
                with target.open("xb") as output:
                    for block in iter(lambda: data.read(1024 * 1024), b""):
                        output.write(block)
                os.chmod(target, entry["mode"])
                _ownership(target, entry)
    for target, entry in links:
        target.symlink_to(entry["target"])
        _ownership(target, entry, follow_symlinks=False)
    for target, entry in reversed(directories):
        os.chmod(target, entry["mode"])
        _ownership(target, entry)
    return compare(manifest, tree_manifest(destination))


def _ownership(path, entry, *, follow_symlinks=True):
    current = path.stat(follow_symlinks=follow_symlinks)
    if (current.st_uid, current.st_gid) != (entry["uid"], entry["gid"]):
        os.chown(path, entry["uid"], entry["gid"], follow_symlinks=follow_symlinks)


def load_manifest(path):
    result = json.loads(Path(path).read_text())
    if result.get("format") != 1 or not isinstance(result.get("entries"), dict):
        raise ValueError("Invalid Site manifest")
    return result


def verify_bundle(archive, expected_components=None):
    """Verify a decrypted outer checkpoint before any restore command runs."""
    files = {}
    with tempfile.TemporaryDirectory(prefix="cc148-verify-") as temporary:
        os.chmod(temporary, 0o700)
        with tarfile.open(archive, "r:") as source:
            for member in source:
                name = member.name
                if (name != Path(name).name or name in ("", ".", "..") or
                        "\\" in name or any(ord(c) < 32 for c in name) or
                        name in files or not member.isfile()):
                    raise ValueError("Unsafe outer checkpoint archive")
                target = Path(temporary) / name
                data = source.extractfile(member)
                if data is None:
                    raise ValueError("Unreadable outer checkpoint component")
                with target.open("xb") as output:
                    for block in iter(lambda: data.read(1024 * 1024), b""):
                        output.write(block)
                os.chmod(target, 0o600)
                files[name] = target
        if len(files) != 6 or set(files).isdisjoint({"site-tree.tar"}) or "site-manifest.json" not in files:
            raise ValueError("Incomplete checkpoint: full Site tree and manifest required")
        native = {name: path for name, path in files.items()
                  if name not in ("site-tree.tar", "site-manifest.json")}
        if len(native) != 4:
            raise ValueError("Incorrect Frappe native component count")
        if sum("database" in name for name in native) != 1 or sum("site_config" in name for name in native) != 1:
            raise ValueError("Missing Frappe native database or configuration")
        if sum("private-files" in name for name in native) != 1 or sum("files" in name and "private" not in name for name in native) != 1:
            raise ValueError("Missing Frappe native file archive")
        for name, path in native.items():
            if "files" in name:
                validate_native_archive(path)
            elif "database" in name:
                if not name.endswith(".gz"):
                    raise ValueError("Compressed database dump required")
                with gzip.open(path, "rb") as database:
                    _digest(database)  # reads through the gzip integrity trailer
            elif "site_config" in name:
                config = json.loads(path.read_text())
                if not isinstance(config, dict) or not config.get("cc_synthetic_dev"):
                    raise ValueError("Synthetic Site configuration missing")
        if expected_components is not None:
            actual = sorted((path.stat().st_size, _file_digest(path)) for path in files.values())
            expected = sorted((item["size"], item["sha256"]) for item in expected_components)
            if len(expected) != 6 or actual != expected:
                raise ValueError("Checkpoint component hash or size mismatch")
        manifest = load_manifest(files["site-manifest.json"])
        result = compare(manifest, tar_manifest(files["site-tree.tar"]))
        return {"components": len(files), "site_entries": result["entries_checked"],
                "site_files": result["files_checked"]}


def _file_digest(path):
    with Path(path).open("rb") as data:
        return _digest(data)


def verify_encrypted(encrypted, key, inventory):
    """Check ciphertext fingerprint, decrypt privately, then validate every member."""
    for value in (encrypted, key, inventory):
        path = Path(value).resolve()
        if any((ancestor / ".git").exists() for ancestor in (path, *path.parents)):
            raise ValueError("Checkpoint material must remain outside Git")
    if (Path(key).is_symlink() or Path(inventory).is_symlink() or
            not Path(key).is_file() or not Path(inventory).is_file() or
            Path(key).stat().st_mode & 0o077 or Path(inventory).stat().st_mode & 0o077):
        raise ValueError("Checkpoint key/inventory must be private regular files")
    report = json.loads(Path(inventory).read_text())
    if _file_digest(encrypted) != report.get("encrypted_sha256"):
        raise ValueError("Encrypted checkpoint hash mismatch")
    if not report.get("components"):
        raise ValueError("Checkpoint inventory or private key mode invalid")
    with tempfile.TemporaryDirectory(prefix="cc148-decrypt-") as temporary:
        os.chmod(temporary, 0o700)
        home = Path(temporary) / "gnupg"
        home.mkdir(mode=0o700)
        clear = Path(temporary) / "backup.tar"
        result = subprocess.run([
            "gpg", "--homedir", str(home), "--batch", "--yes", "--pinentry-mode", "loopback",
            "--passphrase-file", str(key), "--decrypt", "--output", str(clear), str(encrypted)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        if result.returncode:
            raise ValueError("Checkpoint decryption failed")
        os.chmod(clear, 0o600)
        return verify_bundle(clear, report["components"])


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("verify-archive", "verify-tree", "extract", "verify-bundle", "verify-encrypted"))
    parser.add_argument("--archive")
    parser.add_argument("--manifest")
    parser.add_argument("--destination")
    parser.add_argument("--inventory", help="Private checkpoint inventory.json, outside Git")
    parser.add_argument("--encrypted")
    parser.add_argument("--key")
    parser.add_argument("--volatile-logs", action="store_true")
    args = parser.parse_args()
    if args.action == "verify-encrypted":
        if not (args.encrypted and args.key and args.inventory):
            parser.error("--encrypted, --key and --inventory are required")
        result = verify_encrypted(args.encrypted, args.key, args.inventory)
    elif args.action == "verify-bundle":
        report = json.loads(Path(args.inventory).read_text()) if args.inventory else None
        result = verify_bundle(args.archive, report["components"] if report else None)
    else:
        if not args.manifest:
            parser.error("--manifest is required for Site archive/tree operations")
        reference = load_manifest(args.manifest)
    if args.action == "verify-archive":
        result = compare(reference, tar_manifest(args.archive))
    elif args.action == "verify-tree":
        result = compare(reference, tree_manifest(args.destination), volatile_logs=args.volatile_logs)
    elif args.action == "extract":
        result = extract_verified(args.archive, reference, args.destination)
    print(json.dumps({"status": "PASS_OFFLINE_SITE_PARITY", **result}))
