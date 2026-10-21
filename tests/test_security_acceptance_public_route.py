"""The HTTP acceptance must use its own synthetic route, not the UAT route."""

import importlib.util
import os
from pathlib import Path
import unittest
from unittest.mock import patch


MODULE = Path(__file__).resolve().parents[1] / "infra" / "security_acceptance.py"
SPEC = importlib.util.spec_from_file_location("cc_security_acceptance", MODULE)
acceptance = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(acceptance)
LIVE_SPEC = importlib.util.spec_from_file_location(
    "cc_premium_live_acceptance", MODULE.parent / "premium_live_acceptance.py"
)
live = importlib.util.module_from_spec(LIVE_SPEC)
LIVE_SPEC.loader.exec_module(live)


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

    def test_react_write_requires_disposable_item_and_no_public_route(self):
        fixture = {"tag": "CC-HTTP-ABC1234567", "centers": ["A", "B"],
                   "catalog": {"Item": ["CC-HTTP-ABC1234567 SESSION"],
                               "CC Public Booking Route": []}}
        self.assertEqual(live.owned_write(fixture)["item"], fixture["catalog"]["Item"][0])
        fixture["catalog"]["CC Public Booking Route"] = ["Marco"]
        with self.assertRaises(ValueError):
            live.owned_write(fixture)

    def test_acceptance_backend_is_explicitly_scoped(self):
        with patch.dict(os.environ, {"CC_ACCEPTANCE_BACKEND": "another-project"}):
            with self.assertRaises(ValueError):
                acceptance.acceptance_base_url("8082")
        with patch.dict(os.environ, {"CC_ACCEPTANCE_BACKEND": "centrochange-dev-backend-1"}):
            self.assertEqual(acceptance.acceptance_base_url("8082"), "http://127.0.0.1:8082")

    def test_public_replay_accepts_confirmation_without_losing_idempotency(self):
        acceptance.assert_public_replay(
            {"name": "PA-1", "replay": True, "confirmation": {"state": "Pending", "replay": True}}, "PA-1"
        )
        for response in ({"name": "PA-2", "replay": True, "confirmation": {}},
                         {"name": "PA-1", "replay": False, "confirmation": {}},
                         {"name": "PA-1", "replay": True}):
            with self.subTest(response=response), self.assertRaises(AssertionError):
                acceptance.assert_public_replay(response, "PA-1")


if __name__ == "__main__":
    unittest.main()
