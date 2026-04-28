import unittest

from scripts.build_database import DatabaseBuilder
from scripts.video_credit_extraction import build_performer_review_rows
from scripts.video_credit_extraction import extract_video_performers


class VideoCreditExtractionTests(unittest.TestCase):
    def test_extract_video_performers_prefers_description_labels(self):
        result = extract_video_performers(
            title="测试曲目",
            description="Vocal：初音ミク / 可不\nMovie：Example",
        )

        self.assertEqual(result["performers"], ["初音ミク", "可不"])
        self.assertEqual(result["source"], "description_label")
        self.assertEqual(result["confidence"], "high")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_title_feat(self):
        result = extract_video_performers(
            title="测试曲目 feat. 初音ミク & 可不",
            description="",
        )

        self.assertEqual(result["performers"], ["初音ミク", "可不"])
        self.assertEqual(result["source"], "title_feat")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_title_feat_without_space(self):
        result = extract_video_performers(
            title="测试曲目 feat.初音ミク",
            description="",
        )

        self.assertEqual(result["performers"], ["初音ミク"])
        self.assertEqual(result["source"], "title_feat")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_description_next_line(self):
        result = extract_video_performers(
            title="测试曲目",
            description="Music：Example\nVocal\nHatsune Miku",
        )

        self.assertEqual(result["performers"], ["初音ミク"])
        self.assertEqual(result["source"], "description_next_line")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_plural_vocals_label(self):
        result = extract_video_performers(
            title="测试曲目",
            description="Vocals : 初音ミク, 鏡音リン, KAITO",
        )

        self.assertEqual(result["performers"], ["初音ミク", "鏡音リン", "KAITO"])
        self.assertEqual(result["source"], "description_label")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_separator_titles(self):
        result = extract_video_performers(
            title="花結び／Flower＆重音テトSV",
            description="",
        )

        self.assertEqual(result["performers"], ["flower", "重音テト"])
        self.assertEqual(result["source"], "title_separator")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_title_keyword_fallback(self):
        result = extract_video_performers(
            title="MEIKO『ARQETYPE』",
            description="",
        )

        self.assertEqual(result["performers"], ["MEIKO"])
        self.assertEqual(result["source"], "title_keyword")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_supports_vocaloid_group_titles(self):
        result = extract_video_performers(
            title="halyosy - アイムマイン ft. VOCALOIDS [Official Video]",
            description="",
        )

        self.assertEqual(
            result["performers"],
            ["初音ミク", "鏡音リン", "鏡音レン", "巡音ルカ", "KAITO", "MEIKO"],
        )
        self.assertEqual(result["source"], "title_group")
        self.assertFalse(result["needsReview"])

    def test_extract_video_performers_returns_review_row_when_unmatched(self):
        result = extract_video_performers(
            title="测试曲目",
            description="Movie：Example",
        )

        self.assertEqual(result["performers"], [])
        self.assertEqual(result["source"], "none")
        self.assertTrue(result["needsReview"])

    def test_build_performer_review_rows_only_collects_unresolved_entries(self):
        rows = build_performer_review_rows(
            [
                {
                    "id": "song_1",
                    "title": "测试曲目",
                    "videos": [
                        {
                            "videoId": "AbCdEfGhI12",
                            "title": "测试曲目",
                            "sourceKey": "commissioned_original_mv",
                            "sourceName": "书下曲本家 MV Playlist",
                            "description": "Movie：Example",
                            "performerExtraction": {
                                "performers": [],
                                "confidence": "low",
                                "matchedText": "",
                                "needsReview": True,
                            },
                        },
                        {
                            "videoId": "ZyXwVuTsRq9",
                            "title": "测试曲目 feat. 初音ミク",
                            "sourceKey": "commissioned_original_mv",
                            "sourceName": "书下曲本家 MV Playlist",
                            "description": "",
                            "performerExtraction": {
                                "performers": ["初音ミク"],
                                "confidence": "high",
                                "matchedText": "feat. 初音ミク",
                                "needsReview": False,
                            },
                        },
                    ],
                }
            ]
        )

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["videoId"], "AbCdEfGhI12")
        self.assertEqual(rows[0]["songTitle"], "测试曲目")


class DatabaseBuilderPerformerSummaryTests(unittest.TestCase):
    def setUp(self):
        self.builder = DatabaseBuilder(".")
        self.builder.corrections = {}
        self.builder.youtube_source_name = "playlist_videos_test.json"
        self.builder.sekai_musics = []
        self.builder.sekai_music_tags = []
        self.builder.sekai_units = []
        self.builder.aliases = {}
        self.builder.manual_videos = []

    def test_build_database_adds_performer_summary_for_original_sources(self):
        self.builder.youtube_data = {
            "videos": [
                {
                    "songTitle": "测试曲目",
                    "videoId": "AbCdEfGhI12",
                    "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
                    "title": "测试曲目",
                    "description": "Vocal：初音ミク / 可不\nMovie：Example",
                    "channelTitle": "原曲频道",
                    "channelId": "channel-original",
                    "publishedAt": "2026-04-22T08:00:00Z",
                    "thumbnails": self.builder.build_youtube_thumbnails("AbCdEfGhI12"),
                    "position": 1,
                    "sourceKey": "commissioned_original_mv",
                    "sourceName": "书下曲本家 MV Playlist",
                    "sourceKind": "playlist",
                    "sourceUrl": "https://example.com/original",
                    "videoType": "original_mv",
                    "versionBase": "original",
                    "extractors": ["performers", "staff"],
                }
            ]
        }

        database = self.builder.build_database()

        self.assertEqual(database["metadata"]["version"], "2.2.0")
        self.assertEqual(database["songs"][0]["performerSummary"]["performers"], ["初音ミク", "可不"])
        self.assertEqual(
            database["songs"][0]["videos"][0]["performerExtraction"]["source"],
            "description_label",
        )
        self.assertFalse(database["songs"][0]["videos"][0]["performerExtraction"]["needsReview"])


if __name__ == "__main__":
    unittest.main()
