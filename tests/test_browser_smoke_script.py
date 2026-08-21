import json
import unittest
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parents[1]


class BrowserSmokeScriptTests(unittest.TestCase):
    def test_package_exposes_browser_check_with_pinned_playwright(self):
        package = json.loads((BASE_PATH / "package.json").read_text(encoding="utf-8"))
        self.assertTrue(package["private"])
        self.assertEqual(package["scripts"]["check:browser"], "node scripts/browser_smoke_check.mjs")
        self.assertEqual(package["devDependencies"]["playwright"], "1.62.1")

    def test_browser_check_builds_serves_and_closes_its_own_site(self):
        script = (BASE_PATH / "scripts" / "browser_smoke_check.mjs").read_text(encoding="utf-8")
        self.assertIn("spawnSync", script)
        self.assertIn("createServer", script)
        self.assertIn("listen(0, '127.0.0.1'", script)
        self.assertIn("chromium.launch", script)
        self.assertIn("finally", script)
        self.assertIn("server.close", script)

    def test_browser_check_covers_core_flows_and_mobile_cards(self):
        script = (BASE_PATH / "scripts" / "browser_smoke_check.mjs").read_text(encoding="utf-8")
        for marker in (
            "洛基",
            "CRASH THE PARTY",
            "editor.html?tab=video",
            "alias_editor.html",
            "gridTemplateAreas",
            "filter-drawer-trigger",
            "active-filter-count",
            "searchParams.get('q')",
            "page.goBack()",
            "editor.html?tab=staff",
            "staff-role-value",
            "staff-save-role-btn",
            "staff-toggle-ignore-btn",
            "desktopReadingState",
            "Noto Sans SC",
            "songTitlesOverflowing",
            "staff-review-mobile-queue.png",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)


if __name__ == "__main__":
    unittest.main()
