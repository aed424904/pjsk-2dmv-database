import re
import unittest
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parents[1]


class FrontendEntrypointTests(unittest.TestCase):
    EDITOR_SCRIPT_PATHS = (
        "assets/editor_shared.js",
        "assets/manual_video_editor.js",
        "assets/alias_editor.js",
        "assets/staff_review_editor.js",
        "assets/editor_bootstrap.js",
    )

    DEPLOYED_PAGES = (
        "index.html",
        "video_viewer.html",
        "editor.html",
        "music_viewer.html",
        "manual_video_editor.html",
        "alias_editor.html",
    )

    def test_deployed_pages_do_not_require_remote_fonts(self):
        for filename in self.DEPLOYED_PAGES:
            with self.subTest(filename=filename):
                html = (BASE_PATH / filename).read_text(encoding="utf-8")
                self.assertNotIn("fonts.googleapis.com", html)
                self.assertIn('rel="icon"', html)

    def test_legacy_pages_declare_expected_routes(self):
        expected = {
            "music_viewer.html": "music",
            "manual_video_editor.html": "video",
            "alias_editor.html": "alias",
        }
        for filename, route in expected.items():
            with self.subTest(filename=filename):
                html = (BASE_PATH / filename).read_text(encoding="utf-8")
                self.assertIn(f'data-legacy-route="{route}"', html)
                self.assertIn('assets/legacy_redirect.js', html)

    def test_redirect_helper_preserves_query_and_fragment(self):
        script = (BASE_PATH / "assets" / "legacy_redirect.js").read_text(encoding="utf-8")
        self.assertIn("new URLSearchParams(locationObject.search)", script)
        self.assertIn("locationObject.hash", script)
        self.assertIn("params.set('tab', route.tab)", script)
        self.assertIn("locationObject.replace(target)", script)

    def test_editor_loads_external_assets_in_dependency_order(self):
        html = (BASE_PATH / "editor.html").read_text(encoding="utf-8")
        script_paths = tuple(re.findall(r'<script\s+src="([^"]+)"[^>]*></script>', html))
        self.assertIn('<link rel="stylesheet" href="assets/editor.css">', html)
        self.assertEqual(script_paths, self.EDITOR_SCRIPT_PATHS)
        self.assertNotIn("<style>", html)
        self.assertIsNone(re.search(r'<script(?![^>]*\bsrc=)[^>]*>', html))

    def test_editor_assets_keep_existing_namespace_boundaries(self):
        shared = (BASE_PATH / "assets" / "editor_shared.js").read_text(encoding="utf-8")
        video = (BASE_PATH / "assets" / "manual_video_editor.js").read_text(encoding="utf-8")
        alias = (BASE_PATH / "assets" / "alias_editor.js").read_text(encoding="utf-8")
        staff = (BASE_PATH / "assets" / "staff_review_editor.js").read_text(encoding="utf-8")
        bootstrap = (BASE_PATH / "assets" / "editor_bootstrap.js").read_text(encoding="utf-8")

        self.assertIn("function handleFileProtocolAccess()", shared)
        self.assertIn("const ManualVideoEditor = (function()", video)
        self.assertIn("const AliasEditor = (function()", alias)
        self.assertIn("const StaffReviewEditor = (function()", staff)
        self.assertIn("const VALID_TABS = new Set(['video', 'alias', 'staff'])", bootstrap)

    def test_editor_uses_url_driven_accessible_tabs(self):
        html = (BASE_PATH / "editor.html").read_text(encoding="utf-8")
        bootstrap = (BASE_PATH / "assets" / "editor_bootstrap.js").read_text(encoding="utf-8")
        self.assertIn('role="tablist"', html)
        self.assertEqual(len(re.findall(r'<button[^>]+role="tab"', html)), 3)
        self.assertIn("const VALID_TABS = new Set(['video', 'alias', 'staff'])", bootstrap)
        self.assertIn("new URLSearchParams(location.search).get('tab')", bootstrap)
        self.assertIn("history.replaceState", bootstrap)
        self.assertIn("aria-selected", html)
        self.assertIn("ArrowRight", bootstrap)
        self.assertIn("function activateRequestedTab()", bootstrap)
        self.assertIn("rawTab !== null && !VALID_TABS.has(rawTab)", bootstrap)
        self.assertIn("document.body.dataset.editorTab = nextTab", bootstrap)

    def test_index_local_server_fallback_uses_canonical_entrypoint(self):
        script = (BASE_PATH / "assets" / "index.js").read_text(encoding="utf-8")
        self.assertIn("location.pathname.split('/').pop() || 'index.html'", script)
        self.assertNotIn("location.pathname.split('/').pop() || 'music_viewer.html'", script)
        self.assertIn("${fileName}${location.search}${location.hash}", script)


if __name__ == "__main__":
    unittest.main()
