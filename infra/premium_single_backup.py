#!/usr/bin/env python3
"""Gated, full synthetic DEV checkpoint for #148. Never runs setup or migrate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shutil
import subprocess
import sys
import tarfile
import tempfile
from premium_site_checkpoint import compare, tar_manifest, validate_native_archive, verify_bundle

CONTAINER = "centrochange-dev-backend-1"
SITE = "centrochange.local"

def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def run(args):
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"{args[0]} operation failed (exit {result.returncode})")
    return result.stdout.strip()


def outside_repository(path):
    path = Path(path).expanduser().resolve()
    repository = Path(__file__).resolve().parent.parent
    if (path == repository or repository in path.parents or
            any((ancestor / ".git").exists() for ancestor in (path, *path.parents))):
        raise ValueError("Checkpoint and keys must remain outside Git")
    return path


def verify(expected_container, expected_image):
    if not re.fullmatch(r"[0-9a-f]{64}", expected_container):
        raise ValueError("Full expected container ID required")
    if not re.fullmatch(r"sha256:[0-9a-f]{64}", expected_image):
        raise ValueError("Full expected image ID required")
    actual = run(["docker", "inspect", CONTAINER, "--format", "{{.Id}} {{.Image}}"])
    if actual != f"{expected_container} {expected_image}":
        raise RuntimeError("DEV container/image fingerprint changed")
    check = "import json; p='/home/frappe/frappe-bench/sites/centrochange.local/site_config.json'; print(int(bool(json.load(open(p)).get('cc_synthetic_dev'))))"
    if run(["docker", "exec", CONTAINER, "python3", "-c", check]) != "1":
        raise RuntimeError("Synthetic DEV flag absent; aborting backup")


def live_site_manifest():
    """Independent, read-only scan inside DEV; stdout stays in this process."""
    source = (Path(__file__).parent / "premium_site_checkpoint.py").read_text()
    remote = ("import json,sys; scope={'__name__':'site_inventory'}; "
              "exec(sys.stdin.read(),scope); "
              "print(json.dumps(scope['tree_manifest']('/home/frappe/frappe-bench/sites')))" )
    result = subprocess.run(["docker", "exec", "-i", CONTAINER, "python3", "-c", remote],
                            input=source, text=True, capture_output=True, check=False)
    if result.returncode:
        raise RuntimeError("Read-only original Site inventory failed")
    return json.loads(result.stdout)


def checkpoint(destination, key_directory, expected_container, expected_image):
    destination, key_directory = outside_repository(destination), outside_repository(key_directory)
    if destination == key_directory or destination in key_directory.parents or key_directory in destination.parents:
        raise ValueError("Key directory must be separate from checkpoint directory")
    if not shutil.which("gpg"):
        raise RuntimeError("GnuPG unavailable")
    verify(expected_container, expected_image)
    destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    key_directory.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(destination, 0o700)
    os.chmod(key_directory, 0o700)
    nonce = secrets.token_hex(12)
    remote = f"/tmp/cc148-single-stack-checkpoint-{nonce}"
    job = Path(tempfile.mkdtemp(prefix="cc148-checkpoint-", dir=destination))
    os.chmod(job, 0o700)
    raw = job / "raw"
    archive = job / "backup.tar"
    encrypted = job / "backup.tar.gpg"
    key = key_directory / f"{job.name}.key"
    home = job / "gnupg"
    backup_started = False
    try:
        backup_started = True
        run(["docker", "exec", CONTAINER, "bench", "--site", SITE, "backup", "--with-files", "--compress", "--ignore-backup-conf", "--backup-path", remote])
        run(["docker", "cp", f"{CONTAINER}:{remote}", str(raw)])
        os.chmod(raw, 0o700)
        files = list(raw.iterdir())
        kinds = {
            "database": lambda n: "database" in n,
            "public_files": lambda n: "files" in n and "private" not in n,
            "private_files": lambda n: "private-files" in n,
            "configuration": lambda n: "site_config" in n,
        }
        inventory = []
        for kind, matches_kind in kinds.items():
            matches = [p for p in files if matches_kind(p.name)]
            if (len(matches) != 1 or matches[0].is_symlink() or
                    not matches[0].is_file() or not matches[0].stat().st_size):
                raise RuntimeError(f"Missing or ambiguous {kind} component")
            p = matches[0]
            if kind in ("public_files", "private_files"):
                validate_native_archive(p)
            inventory.append({"kind": kind, "size": p.stat().st_size, "sha256": sha256_file(p)})
        if len(files) != 4:
            raise RuntimeError("Unexpected extra backup component; review manually")
        # The Frappe-native files tarballs omit private/uat and other Site state.
        # Stream the *whole* sites volume, then take a second read-only snapshot.
        # Any concurrent change, including a changing log, blocks this checkpoint.
        original_before = live_site_manifest()
        site_archive = job / "site-tree.tar"
        repeat_archive = job / "site-tree-repeat.tar"
        for target in (site_archive, repeat_archive):
            with target.open("xb") as output:
                copied = subprocess.run(
                    ["docker", "exec", CONTAINER, "tar", "-C", "/home/frappe/frappe-bench", "-cf", "-", "sites"],
                    stdout=output, stderr=subprocess.DEVNULL, check=False)
            if copied.returncode:
                raise RuntimeError("Full Site snapshot failed")
        site_manifest = tar_manifest(site_archive)
        compare(original_before, site_manifest)
        compare(site_manifest, tar_manifest(repeat_archive))
        compare(original_before, live_site_manifest())
        repeat_archive.unlink()
        manifest_file = raw / "site-manifest.json"
        with manifest_file.open("x", encoding="utf-8") as output:
            json.dump(site_manifest, output, sort_keys=True)
        os.chmod(manifest_file, 0o600)
        shutil.move(site_archive, raw / "site-tree.tar")
        files.extend((raw / "site-tree.tar", manifest_file))
        for kind, name in (("site_tree", "site-tree.tar"), ("site_manifest", "site-manifest.json")):
            item = raw / name
            inventory.append({"kind": kind, "size": item.stat().st_size, "sha256": sha256_file(item)})
        with tarfile.open(archive, "w") as output:
            for p in files:
                output.add(p, arcname=p.name, recursive=False)
        os.chmod(archive, 0o600)
        verify_bundle(archive)
        with os.fdopen(os.open(key, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600), "w") as stream:
            stream.write(secrets.token_urlsafe(64))
        home.mkdir(mode=0o700)
        run(["gpg", "--homedir", str(home), "--batch", "--yes", "--pinentry-mode", "loopback", "--passphrase-file", str(key), "--symmetric", "--cipher-algo", "AES256", "--output", str(encrypted), str(archive)])
        verified = subprocess.Popen(["gpg", "--homedir", str(home), "--batch", "--pinentry-mode", "loopback", "--passphrase-file", str(key), "--decrypt", str(encrypted)], stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        digest = hashlib.sha256()
        assert verified.stdout is not None
        for chunk in iter(lambda: verified.stdout.read(1024 * 1024), b""):
            digest.update(chunk)
        verified.stdout.close()
        if verified.wait() or digest.hexdigest() != sha256_file(archive):
            raise RuntimeError("Encrypted checkpoint integrity check failed")
        report = {"status": "PASS_BACKUP_ONLY", "site": SITE, "container_id": expected_container, "image_id": expected_image, "components": inventory, "site_entries": len(site_manifest["entries"]), "encrypted_sha256": sha256_file(encrypted), "restore_tested": False, "backup_directory": str(job), "key_directory": str(key_directory)}
        (job / "inventory.json").write_text(json.dumps(report, indent=2) + "\n")
        os.chmod(job / "inventory.json", 0o600)
        return report
    finally:
        if raw.exists():
            shutil.rmtree(raw)
        (job / "site-tree.tar").unlink(missing_ok=True)
        (job / "site-tree-repeat.tar").unlink(missing_ok=True)
        archive.unlink(missing_ok=True)
        if backup_started:
            cleanup = subprocess.run(["docker", "exec", CONTAINER, "rm", "-r", "--", remote], capture_output=True, check=False)
            if cleanup.returncode and sys.exc_info()[0] is None:
                raise RuntimeError("Remote temporary checkpoint cleanup failed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True)
    parser.add_argument("--key-directory", required=True)
    parser.add_argument("--expected-container-id", required=True)
    parser.add_argument("--expected-image-id", required=True)
    parser.add_argument("--execute", action="store_true", help="Required after explicit Owner runtime gate")
    args = parser.parse_args()
    if not args.execute:
        parser.error("No backup performed: --execute and Owner runtime gate required")
    os.umask(0o077)
    print(json.dumps(checkpoint(args.destination, args.key_directory, args.expected_container_id, args.expected_image_id)))
