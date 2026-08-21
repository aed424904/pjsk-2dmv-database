import tempfile
import unittest
from pathlib import Path
from unittest import mock

from scripts.auto_update import is_suspicious_video_count_drop
from scripts.auto_update import get_regeneration_reasons
from scripts.auto_update import normalize_playlist_videos
from scripts.auto_update import publish_staged_outputs
from scripts.auto_update import pull_updates


class AutoUpdateChangeDetectionTests(unittest.TestCase):
    def test_normalization_detects_description_and_channel_changes(self):
        original = [{"videoId": "video", "title": "title", "description": "old", "channelId": "a"}]
        updated = [{"videoId": "video", "title": "title", "description": "new", "channelId": "b"}]

        self.assertNotEqual(normalize_playlist_videos(original), normalize_playlist_videos(updated))

    def test_large_playlist_count_drop_is_suspicious(self):
        self.assertTrue(is_suspicious_video_count_drop(100, 79))

    def test_small_playlist_count_drop_is_allowed(self):
        self.assertFalse(is_suspicious_video_count_drop(100, 80))
        self.assertFalse(is_suspicious_video_count_drop(100, 95))

    def test_staff_alias_change_triggers_regeneration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            output = base / "output"
            manual = base / "manual_data"
            output.mkdir()
            manual.mkdir()
            for name in ("combined_music_data.json", "musics_base.json", "database_v2.json", "aliases.json"):
                (output / name).write_text("{}", encoding="utf-8")
            staff_aliases = manual / "staff_role_aliases.json"
            staff_aliases.write_text("{}", encoding="utf-8")
            old_timestamp = 1_700_000_000
            new_timestamp = old_timestamp + 10
            for path in output.iterdir():
                __import__("os").utime(path, (old_timestamp, old_timestamp))
            __import__("os").utime(staff_aliases, (new_timestamp, new_timestamp))

            with mock.patch("scripts.auto_update.OUTPUT_DIR", str(output)), \
                    mock.patch("scripts.auto_update.MANUAL_DATA_DIR", str(manual)), \
                    mock.patch("scripts.auto_update.load_video_sources", return_value=[]):
                reasons = get_regeneration_reasons([])

            self.assertTrue(any("staff_role_aliases.json" in reason for reason in reasons))

    def test_staff_line_ignore_change_triggers_regeneration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            output = base / "output"
            manual = base / "manual_data"
            output.mkdir()
            manual.mkdir()
            for name in ("combined_music_data.json", "musics_base.json", "database_v2.json", "aliases.json"):
                (output / name).write_text("{}", encoding="utf-8")
            ignored_lines = manual / "staff_line_ignores.json"
            ignored_lines.write_text("[]", encoding="utf-8")
            for path in output.iterdir():
                __import__("os").utime(path, (1_700_000_000, 1_700_000_000))
            __import__("os").utime(ignored_lines, (1_700_000_010, 1_700_000_010))

            with mock.patch("scripts.auto_update.OUTPUT_DIR", str(output)), \
                    mock.patch("scripts.auto_update.MANUAL_DATA_DIR", str(manual)), \
                    mock.patch("scripts.auto_update.load_video_sources", return_value=[]):
                reasons = get_regeneration_reasons([])

            self.assertTrue(any("staff_line_ignores.json" in reason for reason in reasons))

    def test_pull_updates_fast_forwards_explicit_remote_head(self):
        with mock.patch("scripts.auto_update.run_git", return_value=(0, "", "")) as run_git, \
                mock.patch("builtins.print"):
            self.assertTrue(pull_updates("abc123"))

        run_git.assert_called_once_with(["merge", "--ff-only", "abc123"])


class StagedOutputPublishingTests(unittest.TestCase):
    def test_publish_replaces_complete_output_set(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            staging = base / "staging"
            output = base / "output"
            staging.mkdir()
            output.mkdir()
            (staging / "a.json").write_text("new-a", encoding="utf-8")
            (staging / "b.json").write_text("new-b", encoding="utf-8")
            (output / "a.json").write_text("old-a", encoding="utf-8")

            publish_staged_outputs(staging, output, ["a.json", "b.json"])

            self.assertEqual((output / "a.json").read_text(encoding="utf-8"), "new-a")
            self.assertEqual((output / "b.json").read_text(encoding="utf-8"), "new-b")

    def test_publish_restores_previous_outputs_when_replacement_fails(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base = Path(temp_dir)
            staging = base / "staging"
            output = base / "output"
            staging.mkdir()
            output.mkdir()
            for name in ("a.json", "b.json"):
                (staging / name).write_text(f"new-{name}", encoding="utf-8")
                (output / name).write_text(f"old-{name}", encoding="utf-8")

            real_replace = __import__("os").replace
            calls = 0

            def fail_second_replace(source, target):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("simulated publish failure")
                return real_replace(source, target)

            with mock.patch("scripts.auto_update.os.replace", side_effect=fail_second_replace):
                with self.assertRaises(OSError):
                    publish_staged_outputs(staging, output, ["a.json", "b.json"])

            self.assertEqual((output / "a.json").read_text(encoding="utf-8"), "old-a.json")
            self.assertEqual((output / "b.json").read_text(encoding="utf-8"), "old-b.json")


if __name__ == "__main__":
    unittest.main()
