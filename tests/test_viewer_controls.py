import unittest
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parents[1]


class ViewerControlsTests(unittest.TestCase):
    def test_both_viewers_load_shared_controls_and_expose_drawer_markup(self):
        for page_name in ("index.html", "video_viewer.html"):
            with self.subTest(page=page_name):
                html = (BASE_PATH / page_name).read_text(encoding="utf-8")
                self.assertIn('href="assets/viewer_controls.css"', html)
                self.assertIn('src="assets/viewer_controls.js"', html)
                self.assertIn('id="filter-drawer-trigger"', html)
                self.assertIn('aria-controls="sidebar"', html)
                self.assertIn('id="filter-drawer-backdrop"', html)
                self.assertIn('id="filter-drawer-close"', html)
                self.assertIn('id="filter-drawer-done"', html)
                self.assertIn('id="active-filter-count"', html)

    def test_shared_css_turns_the_existing_sidebar_into_a_mobile_drawer(self):
        css = (BASE_PATH / "assets" / "viewer_controls.css").read_text(encoding="utf-8")
        mobile = css.split("@media (max-width: 900px)", 1)[1]
        self.assertIn("body.filter-drawer-open", mobile)
        self.assertIn(".sidebar.is-open", mobile)
        self.assertIn("position: fixed", mobile)
        self.assertIn("height: 100dvh", mobile)
        self.assertIn(".filter-drawer-backdrop.is-open", mobile)
        self.assertIn("@media (prefers-reduced-motion: reduce)", css)

    def test_shared_script_covers_accessibility_and_history_state(self):
        script = (BASE_PATH / "assets" / "viewer_controls.js").read_text(encoding="utf-8")
        for marker in (
            "sidebar.inert",
            "aria-expanded",
            "event.key === 'Escape'",
            "event.key === 'Tab'",
            "lastFocusedElement.focus",
            "new URLSearchParams",
            "params.getAll(group.param)",
            "params.append(group.param",
            "history.pushState",
            "popstate",
        ):
            with self.subTest(marker=marker):
                self.assertIn(marker, script)

    def test_each_viewer_configures_its_filter_and_sort_url_schema(self):
        song_script = (BASE_PATH / "assets" / "index.js").read_text(encoding="utf-8")
        video_script = (BASE_PATH / "assets" / "video_viewer.js").read_text(encoding="utf-8")
        for marker in ("ViewerControls.createUrlState", "filterType: 'tag'", "filterType: 'staff'", "allowedSortFields"):
            with self.subTest(viewer="song", marker=marker):
                self.assertIn(marker, song_script)
        for marker in ("ViewerControls.createUrlState", "filterType: 'types'", "filterType: 'channels'", "allowedSortFields"):
            with self.subTest(viewer="video", marker=marker):
                self.assertIn(marker, video_script)


if __name__ == "__main__":
    unittest.main()
