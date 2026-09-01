import unittest

from scripts.combine_music_data import build_original_mv_date_map
from scripts.combine_music_data import parse_youtube_date
from scripts.combine_music_data import resolve_released_at
from scripts.combine_music_data import resolve_song_type


class CombineMusicDataTests(unittest.TestCase):
    def test_song_type_uses_newly_written_flag(self):
        self.assertEqual(resolve_song_type(True), "original")
        self.assertEqual(resolve_song_type(False), "cover")
        self.assertEqual(resolve_song_type(None), "cover")

    def test_original_mv_date_map_uses_earliest_upload(self):
        payload = {
            "songs": [
                {
                    "sekaiMusicId": 42,
                    "videos": [
                        {"type": "official_2dmv", "uploadDate": "2024-01-01T00:00:00Z"},
                        {"type": "original_mv", "uploadDate": "2023-02-03T04:05:06Z"},
                        {"type": "original_mv", "uploadDate": "2022-02-03T04:05:06Z"},
                    ],
                }
            ]
        }

        dates = build_original_mv_date_map(payload)

        self.assertEqual(dates[42], parse_youtube_date("2022-02-03T04:05:06Z"))

    def test_release_date_prefers_original_mv_upload(self):
        game_release = 1_700_000_000_000
        original_upload = 1_600_000_000_000

        self.assertEqual(resolve_released_at(42, game_release, {42: original_upload}), original_upload)


if __name__ == "__main__":
    unittest.main()
