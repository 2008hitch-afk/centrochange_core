"""Fail-fast tests for the W5 browser runtime gate."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('issue139_install_gate', ROOT / 'infra/issue139_install_gate.py')
gate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(gate)


class BrowserPreflightTests(unittest.TestCase):
    def test_missing_chromium_shared_library_blocks_before_runtime_switch(self):
        with self.assertRaisesRegex(gate.Stop, 'libnspr4.so, libnss3.so'):
            gate.check_browser_libraries('libnspr4.so => not found\nlibnss3.so => not found\n')

    def test_complete_browser_dependency_report_passes(self):
        self.assertEqual(gate.check_browser_libraries('libnspr4.so => /tmp/qa/libnspr4.so (0x1)\n'),
                         {'missing_shared_libraries': []})

    def test_ldd_failure_blocks_closed(self):
        with self.assertRaisesRegex(gate.Stop, 'ldd failed'):
            gate.check_browser_libraries('', returncode=1)


if __name__ == '__main__':
    unittest.main()
