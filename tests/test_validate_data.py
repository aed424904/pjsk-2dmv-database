import json
import shutil
import unittest
import uuid
from pathlib import Path

from scripts.validate_data import DataValidator


class DataValidatorTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
