import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_site import SITE_FILES
from scripts.build_site import build_site


class BuildSiteTests(unittest.TestCase):
    def test_site_allowlist_includes_editor_assets(self):
        expected_assets = {
            "assets/editor.css",
            "assets/editor_shared.js",
            "assets/manual_video_editor.js",
            "assets/alias_editor.js",
            "assets/staff_review_editor.js",
            "assets/editor_bootstrap.js",
        }
        self.assertTrue(expected_assets.issubset(set(SITE_FILES)))

    def test_site_allowlist_includes_viewer_assets(self):
        expected_assets = {
            "assets/index.css",
            "assets/index.js",
            "assets/viewer_controls.css",
            "assets/viewer_controls.js",
            "assets/video_viewer.css",
            "assets/video_viewer.js",
            "output/staff_review.json",
            "manual_data/staff_role_aliases.json",
            "manual_data/staff_name_aliases.json",
            "manual_data/staff_line_ignores.json",
        }
        self.assertTrue(expected_assets.issubset(set(SITE_FILES)))

    def test_build_site_copies_allowlist_and_excludes_project_files(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            for relative_path in SITE_FILES:
                source = base_path / relative_path
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text(json.dumps({"path": relative_path}), encoding="utf-8")
            (base_path / ".git").mkdir()
            (base_path / ".git" / "config").write_text("private", encoding="utf-8")
            (base_path / "backup").mkdir()
            (base_path / "backup" / "old.json").write_text("private", encoding="utf-8")

            dist = build_site(base_path)

            self.assertTrue((dist / "index.html").is_file())
            self.assertTrue((dist / "output" / "database_v2.json").is_file())
            self.assertTrue((dist / "sekai-master-db-diff-main" / "gameCharacters.json").is_file())
            self.assertTrue((dist / "assets" / "legacy_redirect.js").is_file())
            self.assertTrue((dist / "assets" / "editor.css").is_file())
            self.assertTrue((dist / "assets" / "editor_bootstrap.js").is_file())
            self.assertTrue((dist / "assets" / "staff_review_editor.js").is_file())
            self.assertTrue((dist / "output" / "staff_review.json").is_file())
            self.assertTrue((dist / "manual_data" / "staff_line_ignores.json").is_file())
            self.assertTrue((dist / "assets" / "index.css").is_file())
            self.assertTrue((dist / "assets" / "index.js").is_file())
            self.assertTrue((dist / "assets" / "viewer_controls.css").is_file())
            self.assertTrue((dist / "assets" / "viewer_controls.js").is_file())
            self.assertTrue((dist / "assets" / "video_viewer.css").is_file())
            self.assertTrue((dist / "assets" / "video_viewer.js").is_file())
            self.assertTrue((dist / "music_viewer.html").is_file())
            self.assertTrue((dist / "manual_video_editor.html").is_file())
            self.assertTrue((dist / "alias_editor.html").is_file())
            self.assertFalse((dist / ".git").exists())
            self.assertFalse((dist / "backup").exists())

    def test_build_site_replaces_previous_dist(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            for relative_path in SITE_FILES:
                source = base_path / relative_path
                source.parent.mkdir(parents=True, exist_ok=True)
                source.write_text("first", encoding="utf-8")
            dist = build_site(base_path)
            (dist / "stale.txt").write_text("stale", encoding="utf-8")
            (base_path / "index.html").write_text("second", encoding="utf-8")

            build_site(base_path)

            self.assertEqual((dist / "index.html").read_text(encoding="utf-8"), "second")
            self.assertFalse((dist / "stale.txt").exists())


if __name__ == "__main__":
    unittest.main()
