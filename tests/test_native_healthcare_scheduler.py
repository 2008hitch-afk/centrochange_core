"""Scheduler regression: never grant a native bypass of AppointmentMixin."""
import importlib.util
from pathlib import Path
from types import ModuleType, SimpleNamespace
from unittest import TestCase
from unittest.mock import patch
import sys


ROOT = Path(__file__).resolve().parents[1]
FILE = ROOT / "app/centrochange_core/centrochange_core/scheduling/native_scheduler.py"
HOOKS = ROOT / "app/centrochange_core/centrochange_core/hooks.py"
BOOKING = ROOT / "app/centrochange_core/centrochange_core/scheduling/booking.py"


def load_module():
    spec = importlib.util.spec_from_file_location("cc_native_scheduler_test", FILE)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class NativeHealthcareSchedulerTest(TestCase):
    def test_protects_job_without_weakening_appointment_validate(self):
        s = FILE.read_text(encoding="utf8")
        self.assertIn("UPSTREAM_JOB", s)
        self.assertIn("OWN_CATCH_UP", s)
        hooks = HOOKS.read_text(encoding="utf8")
        self.assertIn(
            'after_migrate.append("centrochange_core.scheduling.native_scheduler.configure")',
            hooks,
        )
        booking = BOOKING.read_text(encoding="utf8")
        self.assertIn("if not frappe.flags.get('cc_appointment_write'):", booking)
        self.assertNotIn("cc_native_scheduler_override", booking)

    def test_configuration_stops_only_native_job_and_is_idempotent(self):
        mod = load_module()
        state = {mod.UPSTREAM_JOB: 0, mod.OWN_CATCH_UP: 0}
        writes = []
        fake = ModuleType("frappe")
        fake.get_installed_apps = lambda: ["frappe", "erpnext", "healthcare", "centrochange_core"]
        fake.get_hooks = lambda name: (
            {"cron": {"*/5 * * * *": [mod.OWN_CATCH_UP]}} if name == "scheduler_events" else {}
        )

        def get_all(doctype, filters=None, fields=None, page_length=None):
            self.assertEqual(doctype, "Scheduled Job Type")
            return ([SimpleNamespace(name=filters["method"], stopped=state[filters["method"]])]
                    if filters["method"] in state else [])

        fake.get_all = get_all

        def get_value(doctype, filters, field):
            self.assertEqual(doctype, "Scheduled Job Type")
            self.assertEqual(field, "name")
            return filters["method"]

        def set_value(doctype, name, field, value):
            self.assertEqual((doctype, field), ("Scheduled Job Type", "stopped"))
            self.assertEqual(name, mod.UPSTREAM_JOB)
            state[name] = value
            writes.append((name, value))

        fake.db = SimpleNamespace(get_value=get_value, set_value=set_value)

        def throw(message):
            raise ValueError(message)

        fake.throw = throw
        with patch.dict(sys.modules, {"frappe": fake}):
            result = mod.configure()
            self.assertTrue(result["native_stopped"])
            self.assertTrue(result["cc_catch_up_active"])
            self.assertEqual(writes, [(mod.UPSTREAM_JOB, 1)])
            mod.configure()
            self.assertEqual(writes, [(mod.UPSTREAM_JOB, 1)])
            self.assertEqual(state[mod.OWN_CATCH_UP], 0)

    def test_refuses_missing_or_stopped_cc_catchup(self):
        mod = load_module()
        fake = ModuleType("frappe")
        fake.get_installed_apps = lambda: ["healthcare", "centrochange_core"]
        fake.get_hooks = lambda name: {"cron": {"*/5 * * * *": [mod.OWN_CATCH_UP]}}
        fake.throw = lambda message: (_ for _ in ()).throw(ValueError(message))
        fake.get_all = lambda doctype, filters, fields, page_length: [
            SimpleNamespace(name=filters["method"], stopped=1)
        ]
        with patch.dict(sys.modules, {"frappe": fake}):
            with self.assertRaisesRegex(ValueError, "catch-up job is stopped"):
                mod.configure()
        fake.get_hooks = lambda name: {"cron": {}}
        with patch.dict(sys.modules, {"frappe": fake}):
            with self.assertRaisesRegex(ValueError, "hook not registered"):
                mod.configure()
