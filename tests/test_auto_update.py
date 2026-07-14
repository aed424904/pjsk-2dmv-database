import unittest

from scripts.auto_update import normalize_playlist_videos


class AutoUpdateChangeDetectionTests(unittest.TestCase):
    def test_normalization_detects_description_and_channel_changes(self):
        original = [{"videoId": "video", "title": "title", "description": "old", "channelId": "a"}]
        updated = [{"videoId": "video", "title": "title", "description": "new", "channelId": "b"}]

        self.assertNotEqual(normalize_playlist_videos(original), normalize_playlist_videos(updated))


if __name__ == "__main__":
    unittest.main()
