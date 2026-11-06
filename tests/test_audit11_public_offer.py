"""AUDIT-11: public 20-minute zero-price offer restrictions (pure policy, no Frappe)."""
import importlib.util
from pathlib import Path
import unittest

P = Path(__file__).resolve().parents[1] / "app" / "centrochange_core" / "centrochange_core" / "scheduling" / "public_offer.py"
SPEC = importlib.util.spec_from_file_location("audit11_public_offer", P)
offer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(offer)


class PublicFirstMeetingOfferTests(unittest.TestCase):
    def setUp(self):
        self.mapping = {"sede": "PRIMO-IN-SEDE", "online": "PRIMO-ONLINE"}
        self.profile = {"duration": 20, "cc_price_snapshot": 0, "cc_currency_snapshot": "EUR", "cc_service_label": "Colloquio gratuito in sede"}

    def test_only_exact_modes_and_distinct_appointment_types(self):
        self.assertEqual(offer.configured_type(self.mapping, "sede"), "PRIMO-IN-SEDE")
        self.assertEqual(offer.configured_type(self.mapping, "online"), "PRIMO-ONLINE")
        for mode in ("Marco", "gruppo", "online-extra", "", None, 0):
            with self.subTest(mode=mode), self.assertRaises(offer.PublicOfferError):
                offer.configured_type(self.mapping, mode)
        with self.assertRaises(offer.PublicOfferError):
            offer.configured_type({"sede": "SHARED", "online": "SHARED"}, "sede")
        for config in (None, {}, {"sede": "ONE"}, {"online": "TWO"}, ["WRONG"]):
            with self.subTest(config=config), self.assertRaises(offer.PublicOfferError):
                offer.configured_type(config, "online")

    def test_no_paid_or_long_or_non_eur_public_first_meeting(self):
        self.assertTrue(offer.validate_free_offer(self.profile, 'sede'))
        for changes in ({"duration": 65}, {"duration": 45}, {"duration": 0},
                        {"cc_price_snapshot": 44}, {"cc_price_snapshot": -1},
                        {"cc_price_snapshot": "NaN"}, {"cc_currency_snapshot": "USD"}):
            with self.subTest(changes=changes), self.assertRaises(offer.PublicOfferError):
                offer.validate_free_offer({**self.profile, **changes}, 'sede')

    def test_mode_must_match_item_label_in_internal_agenda(self):
        valid_online = {**self.profile, "cc_service_label": "Colloquio conoscitivo online"}
        self.assertTrue(offer.validate_free_offer(valid_online, "online"))
        with self.assertRaises(offer.PublicOfferError):
            offer.validate_free_offer(valid_online, "sede")
        with self.assertRaises(offer.PublicOfferError):
            offer.validate_free_offer(self.profile, "online")
        with self.assertRaises(offer.PublicOfferError):
            offer.validate_free_offer(self.profile, "gruppo")

    def test_no_missing_money_or_duration(self):
        for key in self.profile:
            with self.subTest(key=key):
                data = dict(self.profile)
                del data[key]
                with self.assertRaises(offer.PublicOfferError):
                    offer.validate_free_offer(data, 'sede')


if __name__ == "__main__":
    unittest.main()
