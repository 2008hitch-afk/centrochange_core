"""App hook composition must retain security guards before presentation hooks."""
import runpy,unittest
from pathlib import Path
from mission97_hooks import EXPECTED

class BeforeRequestHooks(unittest.TestCase):
    def test_guards_and_locale_are_composed_once_in_original_order(self):
        source=Path(__file__).resolve().parent.parent/'app/centrochange_core/centrochange_core/hooks.py'
        hooks=runpy.run_path(str(source))
        before=hooks['before_request']
        after=hooks['after_request']
        self.assertEqual(before,EXPECTED)
        self.assertEqual(after,[
            "centrochange_core.security.response_cache.protect",
            "centrochange_core.operations.client_landing.redirect_launcher",
            "centrochange_core.operations.client_landing.redirect_legacy_operational_routes",
        ])
        self.assertEqual(len(before),len(set(before)))
        self.assertEqual(len(after),len(set(after)))

if __name__=='__main__':unittest.main()
