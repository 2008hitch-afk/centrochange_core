import importlib.util
from pathlib import Path
import unittest


path = Path(__file__).resolve().parents[1] / "issue139_restore_guard.py"
spec = importlib.util.spec_from_file_location("issue139_restore_guard", path)
guard = importlib.util.module_from_spec(spec)
spec.loader.exec_module(guard)

CLONE = "cc139-restore-20261014180000-bootstrap"


class RestoreIsolationTests(unittest.TestCase):
    def test_exec_and_compound_copy_destination_are_scoped(self):
        destination = "/home/frappe/frappe-bench/sites/centrochange.local/private/backups/restore-db.sql.gz"
        self.assertEqual(
            guard.scope_restore_command(
                ["docker", "exec", "-u", "0", guard.DEV_BACKEND, "chown", "frappe:root", destination], CLONE
            )[4], CLONE
        )
        self.assertEqual(
            guard.scope_restore_command(
                ["docker", "cp", "/private/restore-db.sql.gz", guard.DEV_BACKEND + ":" + destination], CLONE
            )[-1], CLONE + ":" + destination
        )

    def test_other_dev_service_and_unscoped_target_are_rejected(self):
        bad = (
            ["docker", "exec", "centrochange-dev-db-1", "true"],
            ["docker", "cp", "/private/file", "centrochange-dev-backend-2:/tmp/file"],
            ["docker", "exec", "-u", "0", guard.DEV_BACKEND, "cat", "centrochange-dev-db-1"],
            ["docker", "rm", guard.DEV_BACKEND],
            ["docker", "cp", "/private/file", guard.DEV_BACKEND + ":/tmp/file"],
        )
        for args in bad:
            with self.subTest(args=args), self.assertRaises(guard.IsolationError):
                guard.scope_restore_command(args, CLONE)

    def test_clone_identity_is_exact(self):
        with self.assertRaises(guard.IsolationError):
            guard.scope_restore_command(["docker", "exec", guard.DEV_BACKEND, "true"], "centrochange-dev-backend-1")


if __name__ == "__main__":
    unittest.main()
