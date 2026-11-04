"""HTTP contract against an explicitly supplied disposable Frappe runtime."""

import os
import unittest
from urllib.error import HTTPError
from urllib.request import HTTPRedirectHandler, build_opener


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


@unittest.skipUnless(os.environ.get("CC_TEST_BASE_URL"), "requires an isolated Frappe runtime")
class PublicBookingUrlRuntimeTest(unittest.TestCase):
    def request(self, path):
        url = os.environ["CC_TEST_BASE_URL"].rstrip("/") + path
        try:
            return build_opener(NoRedirect).open(url, timeout=15)
        except HTTPError as response:
            return response

    def test_public_alias_preserves_query(self):
        with self.request("/primo-incontro?demo=1") as response:
            self.assertEqual(response.status, 302)
            self.assertEqual(response.headers["Location"], "/primo_incontro?demo=1")

    def test_alias_does_not_match_other_paths(self):
        with self.request("/primo-incontro-extra") as response:
            self.assertEqual(response.status, 404)

    def test_canonical_route_is_not_missing(self):
        with self.request("/primo_incontro") as response:
            self.assertIn(response.status, (200, 302))


if __name__ == "__main__":
    unittest.main()
