"""The alert projection must be scoped, deduplicated and clear after closure."""
import ast
from datetime import datetime, timedelta, timezone
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[1] / 'app/centrochange_core/centrochange_core/operations/notifications.py'

class PendingOutcomeTests(unittest.TestCase):
    def test_projection_scope_dedup_and_future_exclusion(self):
        # Exercise the production function body with controlled Frappe boundaries.
        import sys, types
        import contextlib
        from zoneinfo import ZoneInfo
        tree = ast.parse(SOURCE.read_text())
        fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'pending_outcomes')
        fn.decorator_list = []
        tree = ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[]))
        now = datetime(2026, 11, 6, 12, tzinfo=timezone.utc)
        rows = [SimpleNamespace(appointment_date='2026-11-06', practitioner='p1', practitioner_name='A', duration=45, ended=True), SimpleNamespace(appointment_date='2026-11-06', practitioner='p1', practitioner_name='A', duration=45, ended=True), SimpleNamespace(appointment_date='2026-11-06', practitioner='p2', practitioner_name='B', duration=45, ended=False)]
        calls=[]
        guards = types.ModuleType('centrochange_core.security.guards')
        guards.require_center=lambda c: calls.append(('center', c))
        guards.require_operational_center=lambda c: calls.append(('operational', c))
        lifecycle = types.ModuleType('centrochange_core.operations.lifecycle')
        lifecycle.now_utc=lambda: now
        lifecycle.start_utc=lambda r: now - timedelta(hours=2) if r.ended else now + timedelta(hours=1)
        lifecycle.ROME=ZoneInfo('Europe/Rome')
        env={'require_manager':lambda: calls.append(('manager', True)), 'current_rows':lambda dt, filters, fields: calls.append(('filters', filters)) or rows}
        with patch.dict(sys.modules, {'centrochange_core.security.guards': guards, 'centrochange_core.operations.lifecycle': lifecycle}):
            exec(compile(tree, str(SOURCE), 'exec'), env)
            result=env['pending_outcomes']('CENTRO-A')
            self.assertEqual([(x['practitioner'], x['count']) for x in result], [('p1', 2)])
            self.assertIn(('center', 'CENTRO-A'), calls)
            self.assertEqual(next(v for k,v in calls if k=='filters')['cc_center'], 'CENTRO-A')
            rows.clear()
            self.assertEqual(env['pending_outcomes']('CENTRO-A'), [])
            calls.clear()
            def deny():
                raise PermissionError('not manager')
            env['require_manager'] = deny
            with self.assertRaises(PermissionError):
                env['pending_outcomes']('CENTRO-A')
            self.assertEqual(calls, [])

if __name__ == '__main__':
    unittest.main()
