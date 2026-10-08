"""App hook composition must retain security guards before presentation hooks."""
import runpy,unittest
from pathlib import Path
from mission97_hooks import EXPECTED

class BeforeRequestHooks(unittest.TestCase):
    def test_guards_and_locale_are_composed_once_in_original_order(self):
        source=Path(__file__).resolve().parent.parent/'app/centrochange_core/centrochange_core/hooks.py'
        actual=runpy.run_path(str(source))['before_request']
        self.assertEqual(actual,EXPECTED)
        self.assertEqual(len(actual),len(set(actual)))

if __name__=='__main__':unittest.main()
