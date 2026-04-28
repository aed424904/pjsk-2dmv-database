import unittest

from scripts.build_database import DatabaseBuilder


class ManualVideoNormalizationTests(unittest.TestCase):
    def setUp(self):
        self.builder = DatabaseBuilder(".")
        self.builder.corrections = {}
        self.builder.original_video_overrides = {}

    def test_normalize_manual_video_fills_defaults_from_url(self):
        video = self.builder.normalize_manual_video(
            {
                "songTitle": "手动补录曲",
                "title": "手动补录曲 / Vivid BAD SQUAD × 初音ミク",
                "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                "publishedAt": "2026-04-21T12:34:56Z",
            },
            fallback_position=10000,
        )

        self.assertIsNotNone(video)
        self.assertEqual(video["videoId"], "AbCdEfGhI12")
        self.assertEqual(video["url"], "https://www.youtube.com/watch?v=AbCdEfGhI12")
        self.assertEqual(video["position"], 10000)
        self.assertEqual(video["channelTitle"], self.builder.OFFICIAL_CHANNEL_TITLE)
        self.assertEqual(video["channelId"], self.builder.OFFICIAL_CHANNEL_ID)
        self.assertIn("maxres", video["thumbnails"])

    def test_normalize_manual_video_preserves_performer_overrides(self):
        video = self.builder.normalize_manual_video(
            {
                "songTitle": "手动补录曲",
                "title": "手动补录曲",
                "videoId": "AbCdEfGhI12",
                "publishedAt": "2026-04-21T12:34:56Z",
                "performers": ["初音ミク", "可不"],
                "extractors": ["performers", "staff"],
            },
            fallback_position=10000,
        )

        self.assertEqual(video["performers"], ["初音ミク", "可不"])
        self.assertEqual(video["extractors"], ["performers", "staff"])
        self.assertEqual(video["sourceKey"], "manual")
        self.assertEqual(video["sourceKind"], "manual")

    def test_merge_video_sources_skips_duplicate_video_id(self):
        playlist_videos = [
            {
                "videoId": "AbCdEfGhI12",
                "title": "已有视频",
                "description": "",
                "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                "channelTitle": self.builder.OFFICIAL_CHANNEL_TITLE,
                "channelId": self.builder.OFFICIAL_CHANNEL_ID,
                "publishedAt": "2026-04-20T10:00:00Z",
                "thumbnails": {},
                "position": 1,
            }
        ]
        manual_videos = [
            self.builder.normalize_manual_video(
                {
                    "songTitle": "重复曲目",
                    "title": "重复曲目 / Leo/need × 初音ミク",
                    "videoId": "AbCdEfGhI12",
                    "publishedAt": "2026-04-21T10:00:00Z",
                },
                fallback_position=10000,
            ),
            self.builder.normalize_manual_video(
                {
                    "songTitle": "新增曲目",
                    "title": "新增曲目 / Leo/need × 初音ミク",
                    "videoId": "ZyXwVuTsRq9",
                    "publishedAt": "2026-04-21T10:00:00Z",
                },
                fallback_position=10001,
            ),
        ]

        merged = self.builder.merge_video_sources(playlist_videos, manual_videos)
        self.assertEqual(len(merged), 2)
        self.assertEqual(merged[-1]["videoId"], "ZyXwVuTsRq9")

    def test_apply_original_video_override_merges_performers(self):
        self.builder.original_video_overrides = {
            "AbCdEfGhI12": {
                "performers": ["初音ミク"],
            }
        }

        merged = self.builder.apply_original_video_override(
            {
                "videoId": "AbCdEfGhI12",
                "title": "测试曲目",
                "description": "",
                "extractors": ["staff"],
            }
        )

        self.assertEqual(merged["performers"], ["初音ミク"])
        self.assertEqual(merged["extractors"], ["staff", "performers"])

    def test_determine_video_version_detects_sekai_and_april_fool(self):
        version = self.builder.determine_video_version(
            {
                "title": "エイプリルフール2026 セカイver. / Leo/need × 初音ミク",
            }
        )

        self.assertEqual(version["base"], "sekai")
        self.assertIn("april_fool", version["special"])
        self.assertEqual(version["label"], "SEKAI ver / 愚人节版")

    def test_determine_video_version_detects_virtual_singer(self):
        version = self.builder.determine_video_version(
            {
                "title": "炉心融解 / バーチャル・シンガーver.",
            }
        )

        self.assertEqual(version["base"], "virtual_singer")
        self.assertEqual(version["special"], [])

    def test_determine_video_version_uses_cast_segment_for_virtual_singer(self):
        version = self.builder.determine_video_version(
            {
                "title": "Life Will Change / 初音ミク × 鏡音リン × 鏡音レン",
            }
        )

        self.assertEqual(version["base"], "virtual_singer")

    def test_determine_video_version_uses_cast_segment_for_sekai(self):
        version = self.builder.determine_video_version(
            {
                "title": "Fire◎Flower (Rerec) / 東雲彰人 × 青柳冬弥 × 天馬司 × 神代類 × 鏡音レン × KAITO",
            }
        )

        self.assertEqual(version["base"], "sekai")

    def test_determine_video_version_respects_manual_override(self):
        version = self.builder.determine_video_version(
            {
                "title": "任意标题",
                "version": {
                    "base": "original",
                    "special": ["april_fool"],
                }
            }
        )

        self.assertEqual(version["base"], "original")
        self.assertEqual(version["special"], ["april_fool"])
        self.assertEqual(version["source"], "manual_override")


class ManualVideoBuildDatabaseTests(unittest.TestCase):
    def test_build_database_prefers_explicit_song_title(self):
        builder = DatabaseBuilder(".")
        builder.corrections = {}
        builder.youtube_source_name = "playlist_videos_test.json"
        builder.youtube_data = {
            "videos": [
                {
                    "songTitle": "手动指定歌曲名",
                    "videoId": "AbCdEfGhI12",
                    "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                    "title": "这个标题不符合标准格式",
                    "description": "イラスト：测试",
                    "channelTitle": builder.OFFICIAL_CHANNEL_TITLE,
                    "channelId": builder.OFFICIAL_CHANNEL_ID,
                    "publishedAt": "2026-04-21T08:00:00Z",
                    "thumbnails": builder.build_youtube_thumbnails("AbCdEfGhI12"),
                    "position": 10000,
                }
            ]
        }
        builder.sekai_musics = []
        builder.sekai_music_tags = []
        builder.sekai_units = []
        builder.aliases = {}
        builder.manual_videos = []
        builder.original_video_overrides = {}

        database = builder.build_database()

        self.assertEqual(database["songs"][0]["title"], "手动指定歌曲名")
        self.assertEqual(database["songs"][0]["videos"][0]["videoId"], "AbCdEfGhI12")
        self.assertEqual(database["songs"][0]["videos"][0]["version"]["base"], "unknown")
        self.assertEqual(database["songs"][0]["videoVersionSummary"]["bases"], ["unknown"])

    def test_build_database_summarizes_song_video_versions(self):
        builder = DatabaseBuilder(".")
        builder.corrections = {}
        builder.youtube_source_name = "playlist_videos_test.json"
        builder.youtube_data = {
            "videos": [
                {
                    "songTitle": "测试曲目",
                    "videoId": "AbCdEfGhI12",
                    "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                    "title": "测试曲目 / Leo/need × 初音ミク",
                    "description": "",
                    "channelTitle": builder.OFFICIAL_CHANNEL_TITLE,
                    "channelId": builder.OFFICIAL_CHANNEL_ID,
                    "publishedAt": "2026-04-21T08:00:00Z",
                    "thumbnails": builder.build_youtube_thumbnails("AbCdEfGhI12"),
                    "position": 1,
                },
                {
                    "songTitle": "测试曲目",
                    "videoId": "ZyXwVuTsRq9",
                    "url": "https://www.youtube.com/watch?v=ZyXwVuTsRq9",
                    "title": "测试曲目 / バーチャル・シンガーver.",
                    "description": "",
                    "channelTitle": builder.OFFICIAL_CHANNEL_TITLE,
                    "channelId": builder.OFFICIAL_CHANNEL_ID,
                    "publishedAt": "2026-04-22T08:00:00Z",
                    "thumbnails": builder.build_youtube_thumbnails("ZyXwVuTsRq9"),
                    "position": 2,
                },
            ]
        }
        builder.sekai_musics = []
        builder.sekai_music_tags = []
        builder.sekai_units = []
        builder.aliases = {}
        builder.manual_videos = []
        builder.original_video_overrides = {}

        database = builder.build_database()

        self.assertEqual(
            database["songs"][0]["videoVersionSummary"]["bases"],
            ["sekai", "virtual_singer"]
        )

    def test_build_database_uses_manual_performer_override(self):
        builder = DatabaseBuilder(".")
        builder.corrections = {}
        builder.youtube_source_name = "playlist_videos_test.json"
        builder.youtube_data = {
            "videos": [
                {
                    "songTitle": "手动补录曲",
                    "videoId": "AbCdEfGhI12",
                    "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                    "title": "手动补录曲",
                    "description": "Movie：Example",
                    "channelTitle": builder.OFFICIAL_CHANNEL_TITLE,
                    "channelId": builder.OFFICIAL_CHANNEL_ID,
                    "publishedAt": "2026-04-21T08:00:00Z",
                    "thumbnails": builder.build_youtube_thumbnails("AbCdEfGhI12"),
                    "position": 10000,
                    "sourceKey": "manual",
                    "sourceName": "Manual Entry",
                    "sourceKind": "manual",
                    "sourceUrl": "",
                    "extractors": ["performers"],
                    "performers": ["初音ミク", "可不"],
                }
            ]
        }
        builder.sekai_musics = []
        builder.sekai_music_tags = []
        builder.sekai_units = []
        builder.aliases = {}
        builder.manual_videos = []
        builder.original_video_overrides = {}

        database = builder.build_database()

        self.assertEqual(
            database["songs"][0]["videos"][0]["performerExtraction"]["performers"],
            ["初音ミク", "可不"],
        )
        self.assertEqual(
            database["songs"][0]["videos"][0]["performerExtraction"]["source"],
            "manual",
        )

    def test_build_database_uses_original_video_override_file_data(self):
        builder = DatabaseBuilder(".")
        builder.corrections = {}
        builder.youtube_source_name = "playlist_videos_test.json"
        builder.youtube_data = {
            "videos": [
                {
                    "songTitle": "已有原曲",
                    "videoId": "AbCdEfGhI12",
                    "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                    "title": "已有原曲",
                    "description": "Movie：Example",
                    "channelTitle": builder.OFFICIAL_CHANNEL_TITLE,
                    "channelId": builder.OFFICIAL_CHANNEL_ID,
                    "publishedAt": "2026-04-21T08:00:00Z",
                    "thumbnails": builder.build_youtube_thumbnails("AbCdEfGhI12"),
                    "position": 1,
                    "sourceKey": "commissioned_original_mv",
                    "sourceName": "书下曲本家 MV Playlist",
                    "sourceKind": "playlist",
                    "sourceUrl": "https://example.com/original",
                    "extractors": ["staff"],
                }
            ]
        }
        builder.sekai_musics = []
        builder.sekai_music_tags = []
        builder.sekai_units = []
        builder.aliases = {}
        builder.manual_videos = []
        builder.original_video_overrides = {
            "AbCdEfGhI12": {
                "performers": ["初音ミク"],
            }
        }

        database = builder.build_database()

        self.assertEqual(
            database["songs"][0]["videos"][0]["performerExtraction"]["performers"],
            ["初音ミク"],
        )
        self.assertEqual(
            database["songs"][0]["videos"][0]["performerExtraction"]["source"],
            "manual",
        )
