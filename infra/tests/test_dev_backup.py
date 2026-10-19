"""Cryptographic and path regression tests for private DEV backups."""
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "infra"))
import dev_backup


class DevBackupTests(unittest.TestCase):
    def test_short_private_gpg_home_and_encrypted_archive_round_trip(self):
        self.assertIsNotNone(shutil.which("gpg"), "GnuPG is needed for the crypto regression")
        home = dev_backup._new_gpg_home()
        try:
            self.assertEqual(home.stat().st_mode & 0o777, 0o700)
            self.assertLess(len(os.fsencode(home / "S.gpg-agent")), 100)
            with tempfile.TemporaryDirectory(prefix="cc-backup-crypto-") as temporary:
                root = Path(temporary)
                archive, key, encrypted = (root / "site.tar", root / "key", root / "site.tar.gpg")
                payload = b"synthetic database, public files, private files and site config\n" * 128
                archive.write_bytes(payload)
                key.write_text("synthetic-only-test-key\n")
                os.chmod(archive, 0o600)
                os.chmod(key, 0o600)
                decoded = dev_backup.encrypt_and_verify(archive, key, encrypted, home)
                self.assertEqual(decoded, payload)
                self.assertEqual(hashlib.sha256(decoded).digest(), hashlib.sha256(payload).digest())
                self.assertEqual(encrypted.stat().st_mode & 0o777, 0o600)
                self.assertGreater(encrypted.stat().st_size, 0)
        finally:
            shutil.rmtree(home, ignore_errors=True)

    def test_gpg_nonzero_is_a_real_failure_and_private_paths_are_redacted(self):
        completed = subprocess.CompletedProcess([], 2, stdout=b"", stderr=b"gpg: cannot use /private/job/key: agent failed")
        with patch.object(dev_backup.subprocess, "run", return_value=completed):
            with self.assertRaisesRegex(RuntimeError, "exit 2") as caught:
                dev_backup.run_gpg(["gpg", "--decrypt"], redact=("/private/job",))
        self.assertIn("agent failed", str(caught.exception))
        self.assertIn("[PRIVATE_PATH]", str(caught.exception))
        self.assertNotIn("/private/job", str(caught.exception))


if __name__ == "__main__":
    unittest.main()
