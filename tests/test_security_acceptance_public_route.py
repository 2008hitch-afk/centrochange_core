"""The HTTP acceptance must use its own synthetic route, not the UAT route."""

import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "infra" / "security_acceptance.py"
SPEC = importlib.util.spec_from_file_location("cc_security_acceptance", MODULE)
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)


class PublicRouteFixtureTests(unittest.TestCase):
    def test_uses_owned_route_when_persistent_marco_exists(self):
        fixture = {"catalog": {"CC Public Booking Route": ["Francesca"]}}
        self.assertEqual(acceptance.fixture_public_route(fixture), "Francesca")

    def test_missing_or_ambiguous_route_fails_closed(self):
        for routes in ([], ["Marco", "Francesca"], [""]):
            with self.subTest(routes=routes), self.assertRaises(ValueError):
                acceptance.fixture_public_route(
                    {"catalog": {"CC Public Booking Route": routes}}
                )


if __name__ == "__main__":
    unittest.main()
