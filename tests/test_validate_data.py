import json
import shutil
import unittest
import uuid
from pathlib import Path

from scripts.validate_data import DataValidator


class DataValidatorTests(unittest.TestCase):
    def write_database(self, base_path, database):
        base_path.mkdir(parents=True, exist_ok=True)
        database_path = base_path / "database.json"
        database_path.write_text(json.dumps(database), encoding="utf-8")
        return database_path

    def valid_database(self, videos=None):
        videos = videos or [{
            "type": "official_2dmv",
            "videoId": "AbCdEfGhI12",
            "url": "https://www.youtube.com/watch?v=AbCdEfGhI12",
            "title": "test video",
        }]
        return {
            "metadata": {
                "version": "test",
                "generatedAt": "2026-07-10T00:00:00",
                "sources": ["test"],
                "stats": {
                    "totalSongs": 1,
                    "totalVideos": len(videos),
                    "matchedSekai": 1,
                    "videoTypeBreakdown": {"official_2dmv": len(videos)},
                    "unitBreakdown": {"Virtual Singer": 1},
                },
            },
            "songs": [{
                "id": "song_test",
                "sekaiMusicId": 1,
                "title": "test",
                "classification": {"units": ["Virtual Singer"]},
                "videos": videos,
            }],
        }

    def test_video_count_mismatch_fails_validation(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"validator_{uuid.uuid4().hex}"
        try:
            base_path.mkdir(parents=True, exist_ok=True)
            database_path = base_path / "database.json"
            database_path.write_text(
                json.dumps({
                    "metadata": {
                        "version": "test",
                        "generatedAt": "2026-07-10T00:00:00",
                        "sources": [],
                        "stats": {"totalSongs": 1, "totalVideos": 0},
                    },
                    "songs": [{
                        "id": "song_test",
                        "title": "test",
                        "videos": [{"type": "official_2dmv", "videoId": "AbCdEfGhI12", "url": "https://example.com", "title": "test"}],
                    }],
                }),
                encoding="utf-8",
            )

            validator = DataValidator(str(database_path))
            self.assertFalse(validator.validate())
            self.assertTrue(any("totalVideos" in error for error in validator.errors))
        finally:
            shutil.rmtree(base_path, ignore_errors=True)

    def test_duplicate_video_id_fails_validation(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"validator_{uuid.uuid4().hex}"
        try:
            first = self.valid_database()["songs"][0]["videos"][0]
            database = self.valid_database([first, dict(first)])
            database_path = self.write_database(base_path, database)

            validator = DataValidator(str(database_path))
            self.assertFalse(validator.validate())
            self.assertTrue(any("重复的视频 ID" in error for error in validator.errors))
        finally:
            shutil.rmtree(base_path, ignore_errors=True)

    def test_duplicate_sekai_music_id_fails_validation(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"validator_{uuid.uuid4().hex}"
        try:
            database = self.valid_database()
            duplicate_song = dict(database["songs"][0])
            duplicate_song["id"] = "song_duplicate"
            duplicate_song["title"] = "duplicate"
            duplicate_song["videos"] = []
            database["songs"].append(duplicate_song)
            database["metadata"]["stats"]["totalSongs"] = 2
            database["metadata"]["stats"]["unitBreakdown"] = {"Virtual Singer": 2}
            database_path = self.write_database(base_path, database)

            validator = DataValidator(str(database_path))
            self.assertFalse(validator.validate())
            self.assertTrue(any("Sekai Music ID" in error for error in validator.errors))
        finally:
            shutil.rmtree(base_path, ignore_errors=True)

    def test_non_youtube_video_url_fails_validation(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"validator_{uuid.uuid4().hex}"
        try:
            database = self.valid_database()
            database["songs"][0]["videos"][0]["url"] = "https://example.com/video"
            database_path = self.write_database(base_path, database)

            validator = DataValidator(str(database_path))
            self.assertFalse(validator.validate())
            self.assertTrue(any("YouTube URL" in error for error in validator.errors))
        finally:
            shutil.rmtree(base_path, ignore_errors=True)

    def test_video_type_breakdown_mismatch_fails_validation(self):
        base_path = Path.cwd() / "tests" / "_tmp" / f"validator_{uuid.uuid4().hex}"
        try:
            database = self.valid_database()
            database["metadata"]["stats"]["videoTypeBreakdown"] = {"official_2dmv": 0}
            database_path = self.write_database(base_path, database)

            validator = DataValidator(str(database_path))
            self.assertFalse(validator.validate())
            self.assertTrue(any("videoTypeBreakdown" in error for error in validator.errors))
        finally:
            shutil.rmtree(base_path, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
