"""Offline navigation contracts with synthetic patients; not live Frappe evidence."""
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/operations/workspace.py'


class Denied(Exception):
    pass


class Record(dict):
    __getattr__ = dict.__getitem__


class NavigationScopeTests(unittest.TestCase):
    def setUp(self):
        self.manager = True
        self.actor_enabled = True
        self.patients = [Record(name='PAT-A', patient_name='Paziente A', uid='SYNTHETIC-A'),
                         Record(name='PAT-B', patient_name='Paziente B', uid='SYNTHETIC-B')]
        self.practitioners = [Record(name='PRO-A', practitioner_name='Dott.ssa Rossi', user_id='user-a', status='Active'),
                              Record(name='PRO-B', practitioner_name='Dott. Bianchi', user_id='user-b', status='Active')]
        self.assignments = {'CENTRO-A': ['PAT-A'], 'CENTRO-B': ['PAT-B']}
        self.memberships = {'CENTRO-A': ['user-a'], 'CENTRO-B': ['user-b']}
        self.centers = [Record(name='CENTRO-A', branch='Centro A'), Record(name='CENTRO-B', branch='Centro B')]
        self.frappe = types.ModuleType('frappe')
        self.frappe.PermissionError = Denied
        self.frappe.ValidationError = ValueError
        self.frappe.throw = lambda message, exc=ValueError: (_ for _ in ()).throw(exc(message))
        self.frappe.whitelist = lambda **kwargs: lambda fn: fn
        self.frappe.get_list = self.get_list
        self.frappe.get_all = self.get_list
        self.frappe.db = types.SimpleNamespace(get_value=lambda *args, **kwargs: None)
        utils = types.ModuleType('frappe.utils')
        utils.getdate = lambda value: value
        utils.get_time = lambda value: value
        guards = types.ModuleType('centrochange_core.security.guards')
        guards.enabled = lambda: self.actor_enabled
        guards.is_manager = lambda: self.manager
        guards.roles = lambda: ['CC Manager'] if self.manager else ['CC Professional']
        guards.require_center = lambda center: None if self.manager or center == 'CENTRO-A' else self.frappe.throw('Centro negato', Denied)
        guards.current_rows = self.current_rows
        guards.operational_centers = lambda: self.centers if self.manager else self.centers[:1]
        guards.patient_contexts = lambda: {('PAT-A', 'CENTRO-A')}
        guards.practitioner_for = lambda: 'PRO-A'
        notes = types.ModuleType('centrochange_core.operations.notes')
        notes.require_context = lambda *args: None
        booking = types.ModuleType('centrochange_core.scheduling.booking')
        booking.snapshot = lambda *args: {}
        packages = types.ModuleType('centrochange_core.operations.packages')
        packages._balance = lambda *args: {}
        display = types.ModuleType('centrochange_core.uat.display')
        display.operational_aliases = lambda *args: {}
        modules = {
            'frappe': self.frappe, 'frappe.utils': utils,
            'centrochange_core': types.ModuleType('centrochange_core'),
            'centrochange_core.security': types.ModuleType('centrochange_core.security'),
            'centrochange_core.security.guards': guards,
            'centrochange_core.operations': types.ModuleType('centrochange_core.operations'),
            'centrochange_core.operations.notes': notes,
            'centrochange_core.scheduling': types.ModuleType('centrochange_core.scheduling'),
            'centrochange_core.scheduling.booking': booking,
            'centrochange_core.operations.packages': packages,
            'centrochange_core.uat': types.ModuleType('centrochange_core.uat'),
            'centrochange_core.uat.display': display,
        }
        self.modules = patch.dict(sys.modules, modules)
        self.modules.start()
        spec = importlib.util.spec_from_file_location('centrochange_core.operations.workspace', SOURCE)
        self.workspace = importlib.util.module_from_spec(spec)
        sys.modules[spec.name] = self.workspace
        spec.loader.exec_module(self.workspace)

    def tearDown(self):
        self.modules.stop()
        sys.modules.pop('centrochange_core.operations.workspace', None)

    def current_rows(self, doctype, filters=None, fields=None, pluck=None):
        if doctype == 'CC Patient Assignment':
            return self.assignments[filters['center']]
        if doctype == 'CC Center Membership':
            return self.memberships[filters['center']]
        if doctype == 'Healthcare Practitioner':
            return [row for row in self.practitioners
                    if row.user_id in filters['user_id'][1]
                    and row.status == filters['status']
                    and (not filters.get('name') or row.name == filters['name'])]
        if doctype == 'Mode of Payment':
            return []
        return []

    def get_list(self, doctype, filters=None, or_filters=None, **kwargs):
        if doctype == 'Patient':
            rows = self.patients
            if filters and 'name' in filters:
                rows = [row for row in rows if row.name in filters['name'][1]]
            if or_filters:
                term = next(iter(or_filters.values()))[1].strip('%').lower()
                rows = [row for row in rows if term in row.patient_name.lower() or term in row.name.lower()]
            return rows
        return []

    def test_manager_bootstrap_only_contains_selected_center_patients(self):
        self.assertEqual([row.name for row in self.workspace.bootstrap('CENTRO-A')['patients']], ['PAT-A'])
        self.assertEqual([row.name for row in self.workspace.bootstrap('CENTRO-B')['patients']], ['PAT-B'])

    def test_bootstrap_labels_are_scoped_and_identifiers_remain_canonical(self):
        first = self.workspace.bootstrap('CENTRO-A')
        second = self.workspace.bootstrap('CENTRO-B')
        self.assertEqual([(row.name, row.branch) for row in first['centers']],
                         [('CENTRO-A', 'Centro A'), ('CENTRO-B', 'Centro B')])
        self.assertEqual([(row.name, row.practitioner_name) for row in first['practitioners']],
                         [('PRO-A', 'Dott.ssa Rossi')])
        self.assertEqual([(row.name, row.practitioner_name) for row in second['practitioners']],
                         [('PRO-B', 'Dott. Bianchi')])
        self.assertNotIn('PAT-B', [row.name for row in first['patients']])
        self.assertNotIn('PAT-A', [row.name for row in second['patients']])

    def test_manager_search_only_contains_selected_center_patients(self):
        self.assertEqual([row.name for row in self.workspace.patient_search('CENTRO-A')['patients']], ['PAT-A'])
        self.assertEqual([row.name for row in self.workspace.patient_search('CENTRO-B')['patients']], ['PAT-B'])
        self.assertEqual(self.workspace.patient_search('CENTRO-A', 'Paziente B')['patients'], [])
        with self.assertRaises(Denied):
            self.workspace.patient_search('CENTRO-NON-OPERATIVO', 'Paziente')

    def test_empty_assignment_and_disabled_user_fail_closed(self):
        self.assignments['CENTRO-A'] = []
        self.assertEqual(self.workspace.bootstrap('CENTRO-A')['patients'], [])
        self.assertEqual(self.workspace.patient_search('CENTRO-A')['patients'], [])
        self.actor_enabled = False
        with self.assertRaises(Denied):
            self.workspace.patient_search('CENTRO-A')

    def test_professional_scope_and_denied_center(self):
        self.manager = False
        self.assertEqual([row.name for row in self.workspace.patient_search('CENTRO-A')['patients']], ['PAT-A'])
        with self.assertRaises(Denied):
            self.workspace.patient_search('CENTRO-B')
        with self.assertRaises(Denied):
            self.workspace.bootstrap('CENTRO-B')


if __name__ == '__main__':
    unittest.main()
