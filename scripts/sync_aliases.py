#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
同步手动别称到前端输出文件。

输入:
- manual_data/aliases.json
- manual_data/corrections.json (可选)
- output/combined_music_data.json 或 sekai-master-db-diff-main/musics.json

输出:
- output/aliases.json
"""

from __future__ import annotations

import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def normalize_title(title: str) -> str:
    value = unicodedata.normalize("NFKC", title).strip()
    value = re.sub(r"\s*[（(][^()（）]*[)）]\s*", "", value)
    value = re.sub(r"\s*[-－]\s*reloaded\s*[-－]\s*$", "", value, flags=re.IGNORECASE)
    value = re.sub(r"\s+", "", value)
    return value.casefold()


def load_song_catalog(base_path: Path, output_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    combined_path = (output_dir or base_path / "output") / "combined_music_data.json"
    if combined_path.exists():
        songs = load_json(combined_path)
        return [{"id": song["id"], "title": song["title"]} for song in songs]

    master_path = base_path / "sekai-master-db-diff-main" / "musics.json"
    if master_path.exists():
        songs = load_json(master_path)
        return [{"id": song["id"], "title": song["title"]} for song in songs]

    viewer_path = base_path / "sekai viewer_json" / "musics.json"
    if viewer_path.exists():
        songs = load_json(viewer_path)
        return [{"id": song["id"], "title": song["title"]} for song in songs]

    raise FileNotFoundError("未找到歌曲目录数据：combined_music_data.json / musics.json")


def build_title_indexes(songs: List[Dict[str, Any]]) -> Tuple[Dict[str, List[int]], Dict[str, List[int]]]:
    exact_map: Dict[str, List[int]] = {}
    normalized_map: Dict[str, List[int]] = {}

    for song in songs:
        song_id = song.get("id")
        title = song.get("title")
        if song_id is None or not title:
            continue

        exact_map.setdefault(title, []).append(song_id)
        normalized_map.setdefault(normalize_title(title), []).append(song_id)

    return exact_map, normalized_map


def dedupe_aliases(alias_values: List[str]) -> List[str]:
    result: List[str] = []
    seen = set()
    for alias in alias_values:
        if not isinstance(alias, str):
            continue
        cleaned = alias.strip()
        if not cleaned:
            continue
        key = cleaned.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(cleaned)
    return result


def resolve_song_id(
    title: str,
    exact_map: Dict[str, List[int]],
    normalized_map: Dict[str, List[int]],
    title_corrections: Dict[str, str],
) -> Optional[int]:
    candidates = [title]
    corrected = title_corrections.get(title)
    if corrected and corrected not in candidates:
        candidates.append(corrected)

    for candidate in candidates:
        exact_hits = exact_map.get(candidate, [])
        if len(exact_hits) == 1:
            return exact_hits[0]

    for candidate in candidates:
        normalized_hits = normalized_map.get(normalize_title(candidate), [])
        unique_hits = sorted(set(normalized_hits))
        if len(unique_hits) == 1:
            return unique_hits[0]

    return None


def sync_aliases(base_path: Optional[Path] = None, output_dir: Optional[Path] = None) -> Dict[str, Any]:
    base_path = base_path or Path(__file__).resolve().parents[1]
    output_dir = output_dir or Path(os.environ.get("PROJECT_SEKAI_OUTPUT_DIR", base_path / "output"))

    manual_aliases_path = base_path / "manual_data" / "aliases.json"
    if not manual_aliases_path.exists():
        raise FileNotFoundError(f"未找到手动别称文件: {manual_aliases_path}")

    corrections_path = base_path / "manual_data" / "corrections.json"
    title_corrections: Dict[str, str] = {}
    if corrections_path.exists():
        corrections = load_json(corrections_path)
        title_corrections = corrections.get("titleCorrections", {})

    manual_aliases = load_json(manual_aliases_path)
    songs = load_song_catalog(base_path, output_dir)
    exact_map, normalized_map = build_title_indexes(songs)

    exported: Dict[str, List[str]] = {}
    unmatched: List[str] = []

    for title, payload in manual_aliases.items():
        if isinstance(payload, dict):
            alias_values = payload.get("aliases", [])
        else:
            alias_values = payload

        alias_list = dedupe_aliases(alias_values if isinstance(alias_values, list) else [])
        if not alias_list:
            continue

        song_id = resolve_song_id(title, exact_map, normalized_map, title_corrections)
        if song_id is None:
            unmatched.append(title)
            continue

        key = str(song_id)
        existing = exported.setdefault(key, [])
        existing.extend(alias_list)
        exported[key] = dedupe_aliases(existing)

    sorted_export = {
        key: exported[key]
        for key in sorted(exported.keys(), key=lambda value: int(value))
    }

    output_path = output_dir / "aliases.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(sorted_export, f, ensure_ascii=False, indent=2)

    total_aliases = sum(len(values) for values in sorted_export.values())
    summary = {
        "songs": len(sorted_export),
        "aliases": total_aliases,
        "unmatched": unmatched,
        "output_path": str(output_path),
    }

    print(f"[OK] aliases.json generated: {output_path}")
    print(f"[INFO] 已同步 {summary['songs']} 首歌曲，{summary['aliases']} 个别称")
    if unmatched:
        print(f"[WARN] 未匹配到 {len(unmatched)} 个标题: {', '.join(unmatched)}")

    return summary


def main() -> None:
    sync_aliases()


if __name__ == "__main__":
    main()
