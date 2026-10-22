"""Presentation aliases require exact, private UAT ownership; no prefix guessing."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / 'app/centrochange_core/centrochange_core/uat/display.py'
TAG = 'CC-HTTP-UAT0000001'


class Record(dict):
    __getattr__ = dict.__getitem__


class FakeDatabase:
    values = {
        ('Patient', 'PAT-A', 'customer'): 'CUS-A',
        ('Patient', 'PAT-B', 'customer'): 'CUS-B',
        ('Healthcare Practitioner', 'PR-A', 'supplier'): 'SUP-A',
        ('Item', 'ITEM-A', 'item_name'): 'Visita di prova',
        ('Appointment Type', 'TYPE-A', 'appointment_type'): 'Visita di prova',
        ('CC Package Template', 'TEMPLATE-A', 'title'): 'Percorso di prova',
        ('CC Center Service', 'CENTER-SERVICE-A', 'center'): 'CENTER-A',
        ('Sales Invoice', 'INV-A', 'cc_center'): 'CENTER-A',
        ('Bank Transaction', 'BANK-B', 'cc_center'): 'CENTER-B',
        ('CC Incoming Invoice', 'XML-A', 'center'): 'CENTER-A',
        ('Purchase Invoice', 'PUR-A', 'cc_center'): 'CENTER-A',
    }

    def get_value(self, doctype, name, field):
        if isinstance(name, dict):
            if doctype == 'Payment Entry' and name == {'reference_no': TAG + '-Beta-receipt', 'cc_center': 'CENTER-A'}:
                return 'PAY-A'
            return None
        return self.values.get((doctype, name, field))


class DemoDisplayTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        private = Path(self.tmp.name) / 'private/uat'
        private.mkdir(parents=True)
        (private / 'demo.json').write_text(json.dumps({
            'version': 'goal02-demo-v1',
            'fixture': {'tag': TAG, 'centers': ['CENTER-A', 'CENTER-B'],
                        'patients': ['PAT-A', 'PAT-B'], 'practitioners': ['PR-A'],
                        'catalog': {'Appointment Type': ['TYPE-A'], 'Item': ['ITEM-A'],
                                    'CC Package Template': ['TEMPLATE-A'],
                                    'CC Center Service': ['CENTER-SERVICE-A']}},
            'package': 'PACK-A', 'patients': {'Alfa': 'PAT-A'},
            'appointments': {}, 'sources': {}, 'invoices': {'Beta': 'INV-A'},
            'bank': ['BANK-B'], 'incoming': {'classified': 'XML-A', 'payable': 'PUR-A'},
            'fiscal': {},
        }))
        fake_frappe = types.ModuleType('frappe')
        fake_frappe.conf = {'cc_synthetic_dev': 1, 'cc_uat_demo': 1}
        fake_frappe.get_site_path = lambda *parts: str(Path(self.tmp.name).joinpath(*parts))
        fake_frappe.db = FakeDatabase()
        fake_frappe.has_permission = lambda doctype, ptype, doc: True
        fake_demo = types.ModuleType('centrochange_core.uat.demo')
        fake_demo.TAG, fake_demo.VERSION = TAG, 'goal02-demo-v1'
        spec = importlib.util.spec_from_file_location('centrochange_core.uat.display', SOURCE)
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'frappe': fake_frappe, 'centrochange_core.uat.demo': fake_demo}):
            spec.loader.exec_module(module)
        self.display = module
        self.frappe = fake_frappe

    def test_exact_owned_records_and_center_scope(self):
        aliases = self.display.operational_aliases(
            'CENTER-A', [Record(name='PAT-A', patient_name=TAG + ' Alfa'), Record(name='REAL', patient_name='Persona reale')],
            [Record(name='PR-A', practitioner_name=TAG + ' Marco')],
            [{'name': 'TYPE-A', 'cc_service_label': 'Visita di prova'}],
            [{'name': 'PACK-A', 'label': 'Percorso di prova'}],
            [Record(name='CENTER-A', branch=TAG + ' A')], True)
        self.assertEqual(aliases['PAT-A'], 'Paziente 1')
        self.assertEqual(aliases[TAG + ' Marco'], 'Professionista 1')
        self.assertEqual(aliases['TEMPLATE-A'], 'Pacchetto 1')
        self.assertEqual(aliases['CENTER-A'], 'Centro A')
        self.assertNotIn('REAL', aliases)
        finance = self.display.finance_aliases(
            'CENTER-A', [Record(name='CENTER-A', branch=TAG + ' A')],
            [Record(name='CUS-A', customer_name='Cliente di prova')],
            [Record(name='SUP-A', supplier_name='Fornitore di prova')],
            [Record(name='PR-A', practitioner_name=TAG + ' Marco')],
            [Record(name='ITEM-A', item_name='Visita di prova')],
            [{'name': 'PAT-A', 'label': TAG + ' Alfa'}])
        self.assertEqual(finance['CUS-A'], 'Cliente 1')
        self.assertEqual(finance['Patient::PAT-A'], 'Paziente 1')
        self.assertEqual(finance['PatientDisplay::' + TAG + ' Alfa'], 'Paziente 1')
        self.assertNotIn('PAT-A', finance)
        self.assertEqual(finance['PAY-A'], 'Pagamento 1')
        self.assertEqual(finance['INV-A'], 'Fattura paziente 1')
        self.assertNotIn('BANK-B', finance)
        self.frappe.has_permission = lambda doctype, ptype, doc: False
        denied = self.display.finance_aliases('CENTER-A', [], [], [], [], [])
        self.assertNotIn('INV-A', denied)
        self.assertNotIn('PAY-A', denied)
        self.assertNotIn('Patient::PAT-A', denied)

    def test_missing_manifest_or_gate_returns_no_aliases(self):
        path = Path(self.tmp.name) / 'private/uat/demo.json'
        path.unlink()
        self.assertEqual(self.display.operational_aliases('CENTER-A', [], [], [], [], []), {})
        path.write_text(json.dumps({'version': 'wrong', 'fixture': {'tag': TAG}}))
        self.assertEqual(self.display.finance_aliases('CENTER-A', [], [], [], [], []), {})
        self.frappe.conf['cc_synthetic_dev'] = 0
        self.assertEqual(self.display.operational_aliases('CENTER-A', [], [], [], [], []), {})


if __name__ == '__main__':
    unittest.main()
