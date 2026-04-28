#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a lightweight base music dataset for all songs.

Sources:
- (preferred) sekai-master-db-diff-main/musics.json
- (preferred) sekai-master-db-diff-main/musicTags.json
- (fallback) sekai viewer_json/musics.json
- (fallback) sekai viewer_json/musicTag.json
- (optional) sekai-master-db-diff-main/musicOriginals.json
"""

from __future__ import annotations

import json
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional


UNIT_TAG_TO_NAME = {
    "light_music_club": "Leo/need",
    "idol": "MORE MORE JUMP!",
    "street": "Vivid BAD SQUAD",
    "theme_park": "Wonderlands x Showtime",
    "school_refusal": "25-ji, Nightcord de.",
    "vocaloid": "Virtual Singer",
}


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def resolve_catalog_sources(base_path: Path) -> tuple[Path, Path, List[str]]:
    candidates = [
        (
            base_path / "sekai-master-db-diff-main" / "musics.json",
            base_path / "sekai-master-db-diff-main" / "musicTags.json",
            [
                "sekai-master-db-diff-main/musics.json",
                "sekai-master-db-diff-main/musicTags.json",
            ],
        ),
        (
            base_path / "sekai viewer_json" / "musics.json",
            base_path / "sekai viewer_json" / "musicTag.json",
            [
                "sekai viewer_json/musics.json",
                "sekai viewer_json/musicTag.json",
            ],
        ),
    ]

    for musics_path, tags_path, source_labels in candidates:
        if musics_path.exists() and tags_path.exists():
            return musics_path, tags_path, source_labels

    searched = []
    for musics_path, tags_path, _ in candidates:
        searched.extend([str(musics_path), str(tags_path)])
    raise FileNotFoundError("Missing catalog sources. Checked: " + ", ".join(searched))


def format_timestamp(timestamp_ms: Optional[int]) -> Optional[str]:
    if not timestamp_ms:
        return None
    try:
        jst = timezone(timedelta(hours=9))
        dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=jst)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return None


def build_tags_map(tag_rows: List[Dict[str, Any]]) -> Dict[int, List[str]]:
    tags_by_music: Dict[int, List[tuple]] = defaultdict(list)
    for row in tag_rows:
        music_id = row.get("musicId")
        tag_value = row.get("musicTag")
        if music_id is None or tag_value is None:
            continue
        seq = row.get("seq", 0)
        tags_by_music[music_id].append((seq, tag_value))

    result: Dict[int, List[str]] = {}
    for music_id, pairs in tags_by_music.items():
        pairs.sort(key=lambda x: x[0])
        seen = set()
        ordered_tags: List[str] = []
        for _, tag in pairs:
            if tag in seen:
                continue
            seen.add(tag)
            ordered_tags.append(tag)
        result[music_id] = ordered_tags
    return result


def build_original_link_map(original_rows: List[Dict[str, Any]]) -> Dict[int, Optional[str]]:
    result: Dict[int, Optional[str]] = {}
    for row in original_rows:
        music_id = row.get("musicId")
        if music_id is None:
            continue
        result[music_id] = row.get("videoLink") or None
    return result


def main() -> None:
    base_path = Path(__file__).resolve().parents[1]

    musics_path, tags_path, source_labels = resolve_catalog_sources(base_path)

    musics = load_json(musics_path)
    tag_rows = load_json(tags_path)
    tags_map = build_tags_map(tag_rows)

    original_links: Dict[int, Optional[str]] = {}
    original_links_path = base_path / "sekai-master-db-diff-main" / "musicOriginals.json"
    if original_links_path.exists():
        original_links = build_original_link_map(load_json(original_links_path))

    songs: List[Dict[str, Any]] = []
    unit_breakdown: Dict[str, int] = {name: 0 for name in UNIT_TAG_TO_NAME.values()}
    songs_with_original_link = 0

    for music in musics:
        music_id = music.get("id")
        if music_id is None:
            continue

        tags = tags_map.get(music_id, [])
        unit_tags: List[str] = []
        units: List[str] = []
        for tag in tags:
            if tag in UNIT_TAG_TO_NAME:
                unit_tags.append(tag)
                unit_name = UNIT_TAG_TO_NAME[tag]
                if unit_name not in units:
                    units.append(unit_name)

        for unit_name in units:
            unit_breakdown[unit_name] = unit_breakdown.get(unit_name, 0) + 1

        original_link = original_links.get(music_id)
        if original_link:
            songs_with_original_link += 1

        songs.append(
            {
                "id": music_id,
                "seq": music.get("seq"),
                "title": music.get("title"),
                "pronunciation": music.get("pronunciation"),
                "lyricist": music.get("lyricist"),
                "composer": music.get("composer"),
                "arranger": music.get("arranger"),
                "categories": music.get("categories", []),
                "publishedAt": format_timestamp(music.get("publishedAt")),
                "releasedAt": format_timestamp(music.get("releasedAt")),
                "isNewlyWrittenMusic": music.get("isNewlyWrittenMusic", False),
                "isFullLength": music.get("isFullLength", False),
                "tags": tags,
                "unitTags": unit_tags,
                "units": units,
                "originalVideoLink": original_link,
            }
        )

    sources = list(source_labels)
    if original_links_path.exists():
        sources.append("sekai-master-db-diff-main/musicOriginals.json")

    output = {
        "metadata": {
            "version": "1.0.0",
            "generatedAt": datetime.now().isoformat(),
            "sources": sources,
            "stats": {
                "totalSongs": len(songs),
                "songsWithOriginalVideoLink": songs_with_original_link,
                "unitBreakdown": unit_breakdown,
            },
        },
        "songs": songs,
    }

    output_path = base_path / "output" / "musics_base.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"[OK] musics_base.json generated: {output_path}")


if __name__ == "__main__":
    main()
