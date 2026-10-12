"""Offline contracts for the native-first Desk presentation adapter."""

import unittest
from pathlib import Path

from c109_desk_fragments import PAGES, SOURCE, TARGET, fragment, generate


class DeskFragmentsTest(unittest.TestCase):
    def test_generated_asset_matches_canonical_templates(self):
        self.assertEqual(TARGET.read_text(), generate())

    def test_no_website_shell_or_template_values(self):
        for key, name in PAGES.items():
            with self.subTest(key=key):
                data = fragment((SOURCE / f"{name}.html").read_text())
                self.assertIn('id="cc-main"', data["page"])
                self.assertNotIn("cc_ui_sidebar", data["page"])
                self.assertNotIn("uat_demo", data["page"])
                self.assertNotIn("{{", data["page"])
                self.assertNotIn("<script", data["page"])

    def test_rejects_missing_controller_anchor(self):
        bad = '<body class="x"><div class="page-wrapper">No main</div></body>'
        with self.assertRaises(ValueError):
            fragment(bad)

    def test_runtime_does_not_fetch_website_or_parse_html_page(self):
        page = Path(__file__).resolve().parents[1] / "app/centrochange_core/centrochange_core/centro_change_core/page/cc_unified_desk/cc_unified_desk.js"
        source = page.read_text()
        self.assertIn("deskFragments", source)
        self.assertNotIn("DOMParser", source)
        self.assertNotIn("fetch(surface.path", source)
        self.assertIn("/app/cc-audit-event", source)
        self.assertNotIn("audit_view.js", source)


if __name__ == "__main__":
    unittest.main()
