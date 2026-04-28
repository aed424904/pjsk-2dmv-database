import json
import shutil
import unittest
import uuid
from pathlib import Path

from scripts.build_database import DatabaseBuilder
from scripts.video_source_registry import get_preferred_snapshot_for_source
from scripts.video_source_registry import load_video_sources


class VideoSourceRegistryTests(unittest.TestCase):
    def test_get_preferred_snapshot_for_source_uses_source_specific_pattern(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"registry_{uuid.uuid4().hex}"
        try:
            fetch_dir = base_path / "fetch_youtube_playlist"
            fetch_dir.mkdir(parents=True, exist_ok=True)

            older_path = fetch_dir / "playlist_official_2dmv_20260421_101000.json"
            newer_path = fetch_dir / "playlist_official_2dmv_20260422_101000.json"

            older_path.write_text(json.dumps({"videos": [{"videoId": "old"}]}, ensure_ascii=False), encoding="utf-8")
            newer_path.write_text(
                json.dumps({"videos": [{"videoId": "new-1"}, {"videoId": "new-2"}]}, ensure_ascii=False),
                encoding="utf-8",
            )

            preferred = get_preferred_snapshot_for_source(base_path, "official_2dmv")

            self.assertIsNotNone(preferred)
            self.assertEqual(preferred.name, newer_path.name)
        finally:
            shutil.rmtree(base_path, ignore_errors=True)


class DatabaseBuilderMultiSourceTests(unittest.TestCase):
    def test_load_youtube_data_from_sources_merges_multiple_sources(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"builder_{uuid.uuid4().hex}"
        try:
            manual_dir = base_path / "manual_data"
            fetch_dir = base_path / "fetch_youtube_playlist"
            manual_dir.mkdir(parents=True, exist_ok=True)
            fetch_dir.mkdir(parents=True, exist_ok=True)

            sources = [
                {
                    "key": "official_2dmv",
                    "name": "官方 2DMV Playlist",
                    "kind": "playlist",
                    "enabled": True,
                    "url": "https://example.com/official",
                    "videoType": "official_2dmv",
                    "versionBase": "sekai",
                    "extractors": ["staff"],
                },
                {
                    "key": "commissioned_original_mv",
                    "name": "书下曲本家 MV Playlist",
                    "kind": "playlist",
                    "enabled": True,
                    "url": "https://example.com/original",
                    "videoType": "original_mv",
                    "versionBase": "original",
                    "extractors": ["performers", "staff"],
                },
            ]
            (manual_dir / "video_sources.json").write_text(
                json.dumps(sources, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            official_payload = {
                "metadata": {
                    "sourceKey": "official_2dmv",
                    "sourceName": "官方 2DMV Playlist",
                    "sourceKind": "playlist",
                    "sourceUrl": "https://example.com/official",
                    "versionBase": "sekai",
                    "videoType": "official_2dmv",
                },
                "videos": [
                    {
                        "videoId": "AbCdEfGhI12",
                        "title": "测试曲目 / Leo/need × 初音ミク",
                        "description": "動画：omu",
                        "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                        "publishedAt": "2026-04-21T08:00:00Z",
                        "channelTitle": "官方频道",
                        "channelId": "channel-official",
                        "position": 1,
                    }
                ],
            }
            original_payload = {
                "metadata": {
                    "sourceKey": "commissioned_original_mv",
                    "sourceName": "书下曲本家 MV Playlist",
                    "sourceKind": "playlist",
                    "sourceUrl": "https://example.com/original",
                    "versionBase": "original",
                    "videoType": "original_mv",
                },
                "videos": [
                    {
                        "videoId": "ZyXwVuTsRq9",
                        "title": "测试曲目",
                        "description": "Movie：Example",
                        "url": "https://www.youtube.com/watch?v=ZyXwVuTsRq9",
                        "publishedAt": "2026-04-22T08:00:00Z",
                        "channelTitle": "原曲频道",
                        "channelId": "channel-original",
                        "position": 2,
                    }
                ],
            }

            (fetch_dir / "playlist_official_2dmv_20260422_101000.json").write_text(
                json.dumps(official_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (fetch_dir / "playlist_commissioned_original_mv_20260422_101500.json").write_text(
                json.dumps(original_payload, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            builder = DatabaseBuilder(str(base_path))
            builder.video_sources = load_video_sources(base_path)
            youtube_data = builder.load_youtube_data_from_sources()

            self.assertEqual(len(youtube_data["videos"]), 2)
            self.assertEqual(len(builder.youtube_source_names), 2)

            videos_by_id = {video["videoId"]: video for video in youtube_data["videos"]}
            self.assertEqual(videos_by_id["AbCdEfGhI12"]["sourceKey"], "official_2dmv")
            self.assertEqual(videos_by_id["AbCdEfGhI12"]["versionBase"], "sekai")
            self.assertEqual(videos_by_id["AbCdEfGhI12"]["videoType"], "official_2dmv")

            self.assertEqual(videos_by_id["ZyXwVuTsRq9"]["sourceKey"], "commissioned_original_mv")
            self.assertEqual(videos_by_id["ZyXwVuTsRq9"]["versionBase"], "original")
            self.assertEqual(videos_by_id["ZyXwVuTsRq9"]["videoType"], "original_mv")
        finally:
            shutil.rmtree(base_path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
