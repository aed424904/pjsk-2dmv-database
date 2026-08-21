import unittest
from pathlib import Path


BASE_PATH = Path(__file__).resolve().parents[1]


class MobileVideoLayoutTests(unittest.TestCase):
    def test_video_rows_group_complete_metadata_for_mobile_cards(self):
        script = (BASE_PATH / "assets" / "video_viewer.js").read_text(encoding="utf-8")
        self.assertIn('<div class="video-meta">', script)
        for label in ("版本", "频道", "播放", "日期"):
            with self.subTest(label=label):
                self.assertIn(f'data-label="{label}"', script)

    def test_mobile_css_switches_desktop_grid_rows_to_cards(self):
        css = (BASE_PATH / "assets" / "video_viewer.css").read_text(encoding="utf-8")
        self.assertIn(".video-meta {\n  display: contents;\n}", css)
        mobile = css.split("@media (max-width: 900px)", 1)[1]
        self.assertIn(".list-header { display: none; }", mobile)
        self.assertIn("grid-template-areas:", mobile)
        self.assertIn('"type title arrow"', mobile)
        self.assertIn('"meta meta meta"', mobile)
        self.assertIn("content: attr(data-label)", mobile)
        self.assertIn("white-space: normal", mobile)
        self.assertNotIn(".video-date-col { display: none; }", mobile)


if __name__ == "__main__":
    unittest.main()
