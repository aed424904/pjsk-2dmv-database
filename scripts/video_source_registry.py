"""Helpers for configuring and locating external video sources."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


VIDEO_SOURCES_CONFIG_NAME = "video_sources.json"
FETCH_DIR_NAME = "fetch_youtube_playlist"

DEFAULT_VIDEO_SOURCES: List[Dict[str, Any]] = [
    {
        "key": "official_2dmv",
        "name": "官方 2DMV Playlist",
        "kind": "playlist",
        "enabled": True,
        "url": "https://www.youtube.com/playlist?list=PLiFNg5fXiX32G3fNBC7U02t19zVkHAmdD",
        "videoType": "official_2dmv",
        "versionBase": "sekai",
        "extractors": ["staff"],
    },
    {
        "key": "commissioned_original_mv",
        "name": "书下曲本家 MV Playlist",
        "kind": "playlist",
        "enabled": True,
        "url": "https://www.youtube.com/playlist?list=PLiFNg5fXiX32p4RMMDCUpjVEwXOnqyTj_",
        "videoType": "original_mv",
        "versionBase": "original",
        "extractors": ["performers", "staff"],
    },
]


def _sanitize_source_key(value: Any, fallback_index: int) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        raw = f"source_{fallback_index}"
    sanitized = re.sub(r"[^a-z0-9]+", "_", raw).strip("_")
    return sanitized or f"source_{fallback_index}"


def _normalize_string_list(value: Any) -> List[str]:
    if not value:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        return []

    result = []
    seen = set()
    for item in values:
        text = str(item or "").strip()
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def normalize_video_source(raw_source: Dict[str, Any], fallback_index: int) -> Optional[Dict[str, Any]]:
    if not isinstance(raw_source, dict):
        return None

    key = _sanitize_source_key(raw_source.get("key"), fallback_index)
    kind = str(raw_source.get("kind") or "playlist").strip().lower()
    name = str(raw_source.get("name") or raw_source.get("label") or key).strip()
    enabled = bool(raw_source.get("enabled", True))
    url = str(raw_source.get("url") or "").strip()

    if kind == "playlist" and not url:
        return None

    return {
        "key": key,
        "name": name,
        "kind": kind,
        "enabled": enabled,
        "url": url,
        "videoType": str(raw_source.get("videoType") or "").strip() or None,
        "versionBase": str(raw_source.get("versionBase") or "").strip() or None,
        "versionSpecial": _normalize_string_list(raw_source.get("versionSpecial")),
        "extractors": _normalize_string_list(raw_source.get("extractors")),
    }


def load_video_sources(base_path: Any) -> List[Dict[str, Any]]:
    base_path = Path(base_path)
    config_path = base_path / "manual_data" / VIDEO_SOURCES_CONFIG_NAME

    if config_path.exists():
        with config_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
    else:
        payload = DEFAULT_VIDEO_SOURCES

    if isinstance(payload, dict):
        raw_sources = payload.get("sources", [])
    elif isinstance(payload, list):
        raw_sources = payload
    else:
        raw_sources = []

    normalized_sources = []
    for index, raw_source in enumerate(raw_sources):
        normalized = normalize_video_source(raw_source, index)
        if normalized:
            normalized_sources.append(normalized)

    if normalized_sources:
        return normalized_sources

    return [normalize_video_source(source, index) for index, source in enumerate(DEFAULT_VIDEO_SOURCES) if normalize_video_source(source, index)]


def get_snapshot_glob(source_key: str) -> str:
    return f"playlist_{source_key}_*.json"


def iter_source_snapshot_candidates(base_path: Any, source_key: str) -> List[Path]:
    base_path = Path(base_path)
    fetch_dir = base_path / FETCH_DIR_NAME
    if not fetch_dir.exists():
        return []

    candidates = list(fetch_dir.glob(get_snapshot_glob(source_key)))
    if source_key == "official_2dmv":
        candidates.extend(fetch_dir.glob("playlist_videos_*.json"))

    deduped: List[Path] = []
    seen = set()
    for path in sorted(candidates):
        resolved = str(path.resolve())
        if resolved in seen:
            continue
        seen.add(resolved)
        deduped.append(path)
    return deduped


def _load_snapshot_video_count(path: Path) -> Optional[int]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)
        if not isinstance(payload, dict):
            return None
        metadata = payload.get("metadata", {})
        if isinstance(metadata, dict) and metadata.get("status") not in (None, "complete"):
            return None
        videos = payload.get("videos")
        if not isinstance(videos, list) or not videos:
            return None
        return len(videos)
    except Exception:
        return None


def _snapshot_timestamp_key(path: Path) -> Tuple[str, str]:
    """从新旧快照命名中提取时间戳，避免前缀影响新旧顺序。"""
    match = re.search(r"(\d{8}_\d{6})(?=\.json$)", path.name)
    timestamp = match.group(1) if match else ""
    return timestamp, path.name


def get_preferred_snapshot_for_source(base_path: Any, source_key: str) -> Optional[Path]:
    best_path: Optional[Path] = None
    best_key: Tuple[str, str] = ("", "")

    for path in iter_source_snapshot_candidates(base_path, source_key):
        video_count = _load_snapshot_video_count(path)
        if video_count is None:
            continue

        current_key = _snapshot_timestamp_key(path)
        if current_key > best_key:
            best_key = current_key
            best_path = path

    return best_path


def get_preferred_source_snapshots(
    base_path: Any,
    sources: Optional[Iterable[Dict[str, Any]]] = None,
) -> List[Tuple[Dict[str, Any], Path]]:
    if sources is None:
        sources = load_video_sources(base_path)

    preferred: List[Tuple[Dict[str, Any], Path]] = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        path = get_preferred_snapshot_for_source(base_path, source["key"])
        if path is not None:
            preferred.append((source, path))
    return preferred
