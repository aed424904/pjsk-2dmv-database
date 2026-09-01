import re
import unittest
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parents[1]


class ViewerAssetTests(unittest.TestCase):
    PAGES = {
        "index.html": (
            ("assets/index.css", "assets/viewer_controls.css"),
            ("assets/viewer_controls.js", "assets/index.js"),
        ),
        "video_viewer.html": (
            ("assets/video_viewer.css", "assets/viewer_controls.css"),
            ("assets/viewer_controls.js", "assets/video_viewer.js"),
        ),
    }

    def test_viewer_pages_load_only_their_external_page_assets(self):
        for filename, (stylesheets, scripts) in self.PAGES.items():
            with self.subTest(filename=filename):
                html = (BASE_PATH / filename).read_text(encoding="utf-8")
                stylesheet_paths = tuple(re.findall(r'<link\s+rel="stylesheet"\s+href="([^"]+)">', html))
                script_paths = tuple(re.findall(r'<script\s+src="([^"]+)"[^>]*></script>', html))
                self.assertEqual(stylesheet_paths, stylesheets)
                self.assertEqual(script_paths, scripts)
                self.assertNotIn("<style>", html)
                self.assertIsNone(re.search(r'<script(?![^>]*\bsrc=)[^>]*>', html))

    def test_song_viewer_asset_keeps_existing_behavior_boundaries(self):
        script = (BASE_PATH / "assets" / "index.js").read_text(encoding="utf-8")
        self.assertIn("function handleFileProtocolAccess()", script)
        self.assertIn("function renderSongList()", script)
        self.assertIn("function applyFilters(", script)
        self.assertIn("fetch('output/aliases.json'", script)
        self.assertTrue(script.rstrip().endswith("init();"))

    def test_video_viewer_asset_keeps_existing_behavior_boundaries(self):
        script = (BASE_PATH / "assets" / "video_viewer.js").read_text(encoding="utf-8")
        self.assertIn("function handleFileProtocolAccess()", script)
        self.assertIn("function renderVideoList()", script)
        self.assertIn("function applyFilters(", script)
        self.assertIn("fetch('output/database_v2.json'", script)
        self.assertTrue(script.rstrip().endswith("init();"))

    def test_staff_views_group_and_label_music_credits(self):
        song_script = (BASE_PATH / "assets" / "index.js").read_text(encoding="utf-8")
        video_script = (BASE_PATH / "assets" / "video_viewer.js").read_text(encoding="utf-8")

        for script in (song_script, video_script):
            self.assertIn("STAFF_ROLE_GROUPS", script)
            self.assertIn("lyricist", script)
            self.assertIn("composer", script)
            self.assertIn("mastering", script)
            self.assertIn("音乐", script)

    def test_song_viewer_supports_publication_sort_and_fine_grained_filters(self):
        html = (BASE_PATH / "index.html").read_text(encoding="utf-8")
        script = (BASE_PATH / "assets" / "index.js").read_text(encoding="utf-8")

        self.assertIn('data-sort="releasedAt"', html)
        self.assertIn('id="character-filters"', html)
        self.assertIn('id="song-type-filters"', html)
        self.assertIn("function hasOnlyVirtualSingerTeam", script)
        self.assertIn("function getSongCharacterKeys", script)
        self.assertIn("SONG_TYPE_CONFIG", script)
        self.assertIn("'releasedAt'", script)


if __name__ == "__main__":
    unittest.main()
