import json
import tempfile
import unittest
from pathlib import Path

from scripts.enrich_playlist_channels import enrich_snapshot
from scripts.enrich_playlist_channels import resolve_paths


class FakeUnchangedFetcher:
    def fetch_video_details_map(self, video_ids):
        return {video_ids[0]: {"channelTitle": "channel"}}

    def merge_video_details(self, videos, details_map):
        return videos


class PlaylistEnrichmentTests(unittest.TestCase):
    def test_resolve_paths_returns_only_latest_snapshot_per_source(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            base_path = Path(temp_dir)
            manual_dir = base_path / "manual_data"
            fetch_dir = base_path / "fetch_youtube_playlist"
            manual_dir.mkdir()
            fetch_dir.mkdir()
            (manual_dir / "video_sources.json").write_text(json.dumps([{
                "key": "official_2dmv",
                "name": "official",
                "kind": "playlist",
                "enabled": True,
                "url": "https://www.youtube.com/playlist?list=test",
            }]), encoding="utf-8")
            older = fetch_dir / "playlist_official_2dmv_20260812_100000.json"
            newer = fetch_dir / "playlist_official_2dmv_20260812_110000.json"
            for path in (older, newer):
                path.write_text(json.dumps({"videos": [{"videoId": "AbCdEfGhI12"}]}), encoding="utf-8")

            paths = resolve_paths(base_path, [])

            self.assertEqual(paths, [newer])

    def test_enrich_snapshot_does_not_rewrite_unchanged_payload(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "snapshot.json"
            payload = {"metadata": {}, "videos": [{"videoId": "AbCdEfGhI12"}]}
            original = json.dumps(payload, ensure_ascii=False, indent=2)
            path.write_text(original, encoding="utf-8")

            updated = enrich_snapshot(path, FakeUnchangedFetcher())

            self.assertEqual(updated, 0)
            self.assertEqual(path.read_text(encoding="utf-8"), original)


if __name__ == "__main__":
    unittest.main()
