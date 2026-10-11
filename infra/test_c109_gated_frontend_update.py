import unittest

from c109_gated_frontend_update import service_container_id


class FullIdTest(unittest.TestCase):
    def test_full_id_required_for_cgroup_gate(self):
        full = "a" * 64
        calls = []
        def query(*args):
            calls.append(args)
            return full
        self.assertEqual(service_container_id("c-fit-frontend", query), full)
        self.assertIn("--no-trunc", calls[0])
        self.assertIn("label=com.docker.compose.project=centrochange-c109-gated-r7", calls[0])

    def test_short_duplicate_or_empty_ids_rejected(self):
        for value in ("a" * 12, "", "a" * 64 + "\n" + "b" * 64):
            with self.subTest(value=value[:12]):
                with self.assertRaises(RuntimeError):
                    service_container_id("c-fit-frontend", lambda *args: value)
