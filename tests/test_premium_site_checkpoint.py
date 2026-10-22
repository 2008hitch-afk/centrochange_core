"""Offline recovery regressions for the DECISION-064 incomplete restore."""
import io
import gzip
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tarfile
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "infra"))
from premium_site_checkpoint import (ASSET_LINK, compare, extract_verified,
                                     tar_manifest, tree_manifest, verify_bundle,
                                     verify_encrypted, validate_native_archive)


class SiteCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        sites = self.root / "source" / "sites"
        (sites / "centrochange.local/private/uat").mkdir(parents=True)
        (sites / "centrochange.local/private/files").mkdir(parents=True)
        (sites / "centrochange.local/indexes/web_routes").mkdir(parents=True)
        (sites / "centrochange.local/logs").mkdir(parents=True)
        for path, data in {
            "apps.json": b"{}", "apps.txt": b"frappe\ncentrochange_core\n",
            "common_site_config.json": b'{"db_host":"db"}',
            "centrochange.local/site_config.json": b'{"cc_synthetic_dev":1}',
            "centrochange.local/private/uat/demo.json": b'{"credential":"SYNTHETIC-ONLY"}',
            "centrochange.local/private/uat/demo.lock": b"",
            "centrochange.local/private/files/attachment.payload": b"synthetic attachment",
            "centrochange.local/builder_analytics.duckdb": b"synthetic duckdb bytes",
            "centrochange.local/touched_tables.json": b"{}",
            "centrochange.local/indexes/web_routes/MAIN_WRITELOCK": b"",
            "centrochange.local/logs/database.log": b"synthetic log",
        }.items():
            target = sites / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        (sites / "assets").symlink_to(ASSET_LINK)
        self.archive = self.root / "site-tree.tar"
        with tarfile.open(self.archive, "w") as output:
            output.add(sites, arcname="sites")
        self.manifest = tar_manifest(self.archive)

    def _tar_entries(self, names):
        path = self.root / "altered.tar"
        with tarfile.open(self.archive, "r:") as source, tarfile.open(path, "w") as output:
            for member in source:
                if member.name in names:
                    continue
                output.addfile(member, source.extractfile(member) if member.isfile() else None)
        return path

    def _complete_bundle(self):
        outer = self.root / "complete-backup.tar"
        native_tar = self.root / "files.tgz"
        with tarfile.open(native_tar, "w:gz") as output:
            member = tarfile.TarInfo("files/synthetic.txt")
            member.size = 9
            output.addfile(member, io.BytesIO(b"synthetic"))
        manifest = self.root / "site-manifest.json"
        manifest.write_text(json.dumps(self.manifest))
        files = {
            "database.sql.gz": gzip.compress(b"-- synthetic SQL\n"),
            "public-files.tgz": native_tar.read_bytes(),
            "private-files.tgz": native_tar.read_bytes(),
            "site_config.json": b'{"cc_synthetic_dev":1}',
            "site-tree.tar": self.archive.read_bytes(),
            "site-manifest.json": manifest.read_bytes(),
        }
        with tarfile.open(outer, "w") as output:
            for name, content in files.items():
                member = tarfile.TarInfo(name)
                member.size = len(content)
                output.addfile(member, io.BytesIO(content))
        components = [{"kind": name, "size": len(data), "sha256": hashlib.sha256(data).hexdigest()}
                      for name, data in files.items()]
        return outer, components

    def test_entire_site_restores_with_private_uat_indexes_logs_and_metadata(self):
        result = extract_verified(self.archive, self.manifest, self.root / "restored")
        self.assertGreaterEqual(result["files_checked"], 11)
        compare(self.manifest, tree_manifest(self.root / "restored"))
        (self.root / "restored/centrochange.local/private/uat/demo.json").unlink()
        with self.assertRaisesRegex(ValueError, "Missing required Site state"):
            compare(self.manifest, tree_manifest(self.root / "restored"))

    def test_original_four_component_backup_is_incomplete(self):
        complete, _ = self._complete_bundle()
        outer = self.root / "old-backup.tar"
        with tarfile.open(complete, "r:") as source, tarfile.open(outer, "w") as output:
            for member in source:
                if member.name not in ("site-tree.tar", "site-manifest.json"):
                    output.addfile(member, source.extractfile(member))
        with tarfile.open(self.root / "files.tgz", "r:gz") as native:
            self.assertEqual(native.getnames(), ["files/synthetic.txt"])
        with self.assertRaisesRegex(ValueError, "Incomplete checkpoint"):
            verify_bundle(outer)

    def test_complete_bundle_and_component_hashes(self):
        outer, components = self._complete_bundle()
        self.assertEqual(verify_bundle(outer, components)["components"], 6)
        components[0]["sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "hash or size mismatch"):
            verify_bundle(outer, components)

    @unittest.skipUnless(shutil.which("gpg"), "GnuPG required")
    def test_encrypted_checkpoint_fingerprint_and_decryption(self):
        outer, components = self._complete_bundle()
        encrypted = self.root / "backup.tar.gpg"
        key = self.root / "key"
        key.write_text("SYNTHETIC-TEST-PASSPHRASE")
        key.chmod(0o600)
        subprocess.run(["gpg", "--batch", "--yes", "--pinentry-mode", "loopback",
                        "--passphrase-file", str(key), "--symmetric", "--cipher-algo", "AES256",
                        "--output", str(encrypted), str(outer)], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        report = self.root / "inventory.json"
        report.write_text(json.dumps({"encrypted_sha256": hashlib.sha256(encrypted.read_bytes()).hexdigest(),
                                      "components": components}))
        report.chmod(0o600)
        self.assertEqual(verify_encrypted(encrypted, key, report)["components"], 6)
        encrypted.write_bytes(encrypted.read_bytes() + b"x")
        with self.assertRaisesRegex(ValueError, "Encrypted checkpoint hash mismatch"):
            verify_encrypted(encrypted, key, report)

    def test_missing_uat_manifest_or_any_other_member_fails(self):
        for missing in ("sites/centrochange.local/private/uat/demo.json",
                        "sites/centrochange.local/builder_analytics.duckdb",
                        "sites/centrochange.local/touched_tables.json",
                        "sites/centrochange.local/indexes/web_routes/MAIN_WRITELOCK"):
            with self.subTest(missing=missing):
                altered = self._tar_entries({missing})
                with self.assertRaises(ValueError):
                    compare(self.manifest, tar_manifest(altered))

    def test_changed_content_fails_sha_comparison(self):
        restored = self.root / "restored"
        extract_verified(self.archive, self.manifest, restored)
        (restored / "centrochange.local/private/uat/demo.json").write_text("changed")
        with self.assertRaisesRegex(ValueError, "differs"):
            compare(self.manifest, tree_manifest(restored))

    def test_traversal_and_unsafe_symlinks_fail(self):
        for name, kind, link in (("sites/../escape", "file", None),
                                 ("/sites/escape", "file", None),
                                 ("sites/centrochange.local/private/uat/link", "link", "../../../../etc/passwd"),
                                 ("sites/assets", "link", "/etc/passwd")):
            with self.subTest(name=name):
                path = self.root / "evil.tar"
                with tarfile.open(path, "w") as output:
                    member = tarfile.TarInfo(name)
                    if kind == "link":
                        member.type = tarfile.SYMTYPE
                        member.linkname = link
                        output.addfile(member)
                    else:
                        member.size = 1
                        output.addfile(member, io.BytesIO(b"x"))
                with self.assertRaises(ValueError):
                    tar_manifest(path)

    def test_native_file_archive_traversal_is_rejected(self):
        path = self.root / "native.tgz"
        with tarfile.open(path, "w:gz") as output:
            member = tarfile.TarInfo("../../site_config.json")
            member.size = 1
            output.addfile(member, io.BytesIO(b"x"))
        with self.assertRaisesRegex(ValueError, "Unsafe native"):
            validate_native_archive(path)

    def test_outer_bundle_path_traversal_is_rejected(self):
        path = self.root / "outer.tar"
        with tarfile.open(path, "w") as output:
            member = tarfile.TarInfo("../backup.tar")
            member.size = 1
            output.addfile(member, io.BytesIO(b"x"))
        with self.assertRaisesRegex(ValueError, "Unsafe outer"):
            verify_bundle(path)

    def test_duplicate_and_hardlink_fail(self):
        for kind in ("duplicate", "hardlink"):
            with self.subTest(kind=kind):
                path = self.root / "evil.tar"
                with tarfile.open(path, "w") as output:
                    output.add(self.root / "source/sites", arcname="sites")
                    member = tarfile.TarInfo("sites/apps.txt")
                    if kind == "hardlink":
                        member.type = tarfile.LNKTYPE
                        member.linkname = "sites/apps.json"
                    output.addfile(member)
                with self.assertRaises(ValueError):
                    tar_manifest(path)

    def test_restore_destination_must_be_empty(self):
        target = self.root / "restored"
        target.mkdir()
        (target / "existing").write_text("keep")
        with self.assertRaisesRegex(ValueError, "empty"):
            extract_verified(self.archive, self.manifest, target)
        self.assertEqual((target / "existing").read_text(), "keep")


if __name__ == "__main__":
    unittest.main()
