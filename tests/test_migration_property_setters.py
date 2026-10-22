"""Regression for repeated after_migrate Property Setter churn (issue #150)."""
import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch


SOURCE = (Path(__file__).resolve().parents[1] / "app/centrochange_core"
          / "centrochange_core/security/install.py")


def load_install(existing):
    frappe = ModuleType("frappe")
    frappe.get_all = lambda *args, **kwargs: existing
    custom = ModuleType("frappe.custom")
    doctype = ModuleType("frappe.custom.doctype")
    field_package = ModuleType("frappe.custom.doctype.custom_field")
    field = ModuleType("frappe.custom.doctype.custom_field.custom_field")
    field.create_custom_fields = lambda *args, **kwargs: None
    setter_package = ModuleType("frappe.custom.doctype.property_setter")
    setter = ModuleType("frappe.custom.doctype.property_setter.property_setter")
    calls = []
    setter.make_property_setter = lambda *args, **kwargs: calls.append((args, kwargs))
    modules = {item.__name__: item for item in
               (frappe, custom, doctype, field_package, field, setter_package, setter)}
    with patch.dict(sys.modules, modules):
        spec = importlib.util.spec_from_file_location("tested_security_install", SOURCE)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    return module, calls


class PropertySetterMigrationTest(unittest.TestCase):
    def test_unchanged_setter_does_not_create_audit_churn(self):
        install, calls = load_install([SimpleNamespace(
            value="2", property_type="Int", is_system_generated=1)])
        install.ensure_property_setter("Patient", "allergies", "permlevel", 2, "Int")
        self.assertEqual(calls, [])

    def test_missing_setter_is_created(self):
        install, calls = load_install([])
        install.ensure_property_setter("Patient", "allergies", "permlevel", 2, "Int")
        self.assertEqual(calls, [(("Patient", "allergies", "permlevel", 2, "Int"),
                                  {"validate_fields_for_doctype": False})])

    def test_changed_setter_is_corrected(self):
        install, calls = load_install([SimpleNamespace(
            value="1", property_type="Int", is_system_generated=1)])
        install.ensure_property_setter("Patient", "allergies", "permlevel", 2, "Int")
        self.assertEqual(len(calls), 1)


if __name__ == "__main__":
    unittest.main()
