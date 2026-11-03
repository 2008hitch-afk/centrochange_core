"""AUDIT-11: public mode must be explicitly selected on guest endpoints.

Structural checks only: they do NOT attest live Frappe HTTP behavior.
"""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "app/centrochange_core/centrochange_core/scheduling/public_booking.py"
CONFIRM = ROOT / "app/centrochange_core/centrochange_core/operations/booking_confirmation.py"
ACCEPTANCE = ROOT / "app/centrochange_core/centrochange_core/operations/confirmation_acceptance.py"
SECURITY = ROOT / "infra/security_acceptance.py"


def parameter_is_required(path, function, parameter):
    syntax = ast.parse(path.read_text(encoding="utf-8"))
    fn = next(node for node in syntax.body
              if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function)
    positional = [arg.arg for arg in fn.args.args]
    return parameter in positional[:len(positional) - len(fn.args.defaults)]


class RequiredBookingModeTests(unittest.TestCase):
    def test_mode_is_required_for_all_guest_booking_entrypoints(self):
        for path, fn in ((PUBLIC, "first_meeting"), (PUBLIC, "available_slots"),
                         (CONFIRM, "confirm")):
            with self.subTest(function=fn):
                self.assertTrue(parameter_is_required(path, fn, "mode"))

    def test_isolated_synthetic_callers_supply_explicit_mode(self):
        confirmation_code = ACCEPTANCE.read_text(encoding="utf-8")
        security_code = SECURITY.read_text(encoding="utf-8")
        self.assertIn("'mode':'sede'", confirmation_code)
        self.assertIn("mode='sede'", confirmation_code)
        self.assertIn("'mode':'sede'", security_code)
        self.assertIn("Refuse to mutate non-test-owned Appointment Type", security_code)

    def test_legacy_appointment_type_fixture_cannot_be_assumed(self):
        src = SECURITY.read_text(encoding="utf-8")
        self.assertIn("public_doc['appointment_type'] in fixture['catalog']['Appointment Type']", src)
        self.assertIn("float(public_doc['cc_price_snapshot'])==0", src)
        self.assertIn("public_doc['appointment_type'],'fieldname':'cc_first_meeting'", src)

    def test_both_endpoints_enforce_rome_120_day_future_horizon(self):
        code = PUBLIC.read_text(encoding="utf-8")
        syntax = ast.parse(code)
        self.assertIn("ZoneInfo('Europe/Rome')", code)
        self.assertIn("timedelta(days=120)", code)

        for fn_name in ("first_meeting", "available_slots"):
            with self.subTest(function=fn_name):
                fn = next(node for node in syntax.body
                          if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == fn_name)
                fn_source = ast.get_source_segment(code, fn)
                self.assertIn("timedelta(days=120)", fn_source, f"{fn_name} must enforce 120 days horizon")
                self.assertIn("Scegli una data futura entro 120 giorni.", fn_source, f"{fn_name} must reject horizon breach")

    def test_available_slots_breaks_projection_at_horizon(self):
        code = PUBLIC.read_text(encoding="utf-8")
        syntax = ast.parse(code)
        fn = next(node for node in syntax.body
                  if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == "available_slots")
        fn_source = ast.get_source_segment(code, fn)
        self.assertIn("day>horizon", fn_source)
        self.assertIn("break", fn_source)

    def test_first_meeting_does_not_disclose_email_identity(self):
        code = PUBLIC.read_text(encoding="utf-8")
        # Must not leak email existence to public caller
        self.assertNotIn("L’identità esiste già", code)
        self.assertIn("PUBLIC_FIRST_MEETING_POTENTIAL_DUPLICATE", code)

    def test_confirmation_email_communicates_zero_euro_and_44_euro_next_session(self):
        code = CONFIRM.read_text(encoding="utf-8")
        self.assertIn("Importo dovuto per la prenotazione online: 0 €", code)
        self.assertIn("La prima seduta completa successiva costa 44 €", code)
        self.assertIn("Nessuna seconda seduta o addebito anticipato è stato effettuato con questa richiesta", code)
        self.assertIn("Pending", code)

    def test_frontend_communicates_zero_euro_and_44_euro_next_session(self):
        code = (ROOT / "frontend/premium/src/first_meeting.tsx").read_text(encoding="utf-8")
        self.assertIn("Totale dovuto online", code)
        self.assertIn("Prima seduta successiva", code)
        self.assertIn("44 €", code)
        self.assertIn("0 €", code)
        self.assertIn("pagata solo al momento della seduta", code)


if __name__ == "__main__":
    unittest.main()
