#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Backfill playlist snapshots with actual video uploader channels."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

BASE_PATH = Path(__file__).resolve().parents[1]
if str(BASE_PATH) not in sys.path:
    sys.path.insert(0, str(BASE_PATH))

from fetch_youtube_playlist.fetch_youtube_playlist import DEFAULT_API_KEY
from fetch_youtube_playlist.fetch_youtube_playlist import YouTubePlaylistFetcher
from scripts.video_source_registry import get_preferred_source_snapshots


def load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path: Path, payload: Dict[str, Any]) -> None:
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def unique_video_ids(videos: Iterable[Dict[str, Any]]) -> List[str]:
    ids: List[str] = []
    seen = set()
    for video in videos:
        video_id = str(video.get("videoId") or "").strip()
        if not video_id or video_id in seen:
            continue
        seen.add(video_id)
        ids.append(video_id)
    return ids


def enrich_snapshot(path: Path, fetcher: YouTubePlaylistFetcher) -> int:
    payload = load_json(path)
    videos = payload.get("videos", [])
    if not isinstance(videos, list) or not videos:
        print(f"[SKIP] {path.name}: no videos")
        return 0

    details_map = fetcher.fetch_video_details_map(unique_video_ids(videos))
    if not details_map:
        print(f"[WARN] {path.name}: no details fetched")
        return 0

    enriched_videos = fetcher.merge_video_details(videos, details_map)
    if enriched_videos == videos:
        print(f"[SKIP] {path.name}: details unchanged")
        return 0

    payload["videos"] = enriched_videos
    metadata = payload.setdefault("metadata", {})
    metadata["channelEnrichedAt"] = datetime.now().isoformat()
    metadata["channelEnrichment"] = {
        "source": "youtube.videos.list",
        "updatedVideos": len(details_map),
    }
    save_json(path, payload)
    print(f"[OK] {path.name}: enriched {len(details_map)} videos")
    return len(details_map)


def resolve_paths(base_path: Path, selected_paths: List[str]) -> List[Path]:
    if selected_paths:
        return [Path(path).resolve() for path in selected_paths]

    return [path for _, path in get_preferred_source_snapshots(base_path)]


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", help="Snapshot JSON paths. Defaults to all fetch_youtube_playlist/playlist_*.json")
    parser.add_argument("--api-key", default=DEFAULT_API_KEY, help="YouTube Data API key")
    args = parser.parse_args()

    if not args.api_key:
        raise SystemExit("Missing YouTube API key. Pass --api-key or set YOUTUBE_API_KEY.")

    paths = resolve_paths(BASE_PATH, args.paths)
    fetcher = YouTubePlaylistFetcher(api_key=args.api_key)

    total = 0
    for path in paths:
        total += enrich_snapshot(path, fetcher)

    print(f"[DONE] enriched {total} video details across {len(paths)} snapshots")


if __name__ == "__main__":
    main()
