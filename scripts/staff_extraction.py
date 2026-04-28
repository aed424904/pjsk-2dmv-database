"""Helpers for extracting structured staff data from video descriptions."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Dict, List, Tuple


CANONICAL_ROLES = (
    "illustrator",
    "pvCreator",
    "illustrationAnimation",
    "lyricDesign",
    "animation",
    "design",
    "cg3d",
    "unknown",
)

DEFAULT_ROLE_ALIASES = {
    "イラスト": "illustrator",
    "Illustrator": "illustrator",
    "Illustration": "illustrator",
    "Illust": "illustrator",
    "動画": "pvCreator",
    "映像": "pvCreator",
    "Movie": "pvCreator",
    "Video": "pvCreator",
    "Movie Editor": "pvCreator",
    "Director": "pvCreator",
    "Composite": "pvCreator",
    "編集": "pvCreator",
    "イラストアニメーション": "illustrationAnimation",
    "アニメーション": "animation",
    "アニメーター": "animation",
    "アニメーション制作": "animation",
    "Animation": "animation",
    "Animator": "animation",
    "リリックデザイン": "lyricDesign",
    "Graphic Designer": "design",
    "Design": "design",
    "デザイン": "design",
    "ロゴ": "design",
    "ロゴデザイン": "design",
    "Logo": "design",
    "Logo Designer": "design",
    "アイテムデザイン": "design",
    "グラフィックデザイン": "design",
    "モーショングラフィックデザイン": "design",
    "Character Designer": "design",
    "キャラクターデザイン": "design",
    "色彩設計": "design",
    "背景": "design",
    "Background Artist": "design",
    "3DCG": "cg3d",
    "CG": "cg3d",
    "監督": "pvCreator",
    "撮影監督": "pvCreator",
    "撮影": "pvCreator",
}

DEFAULT_NAME_ALIASES: Dict[str, str] = {}

BASE_PATH = Path(__file__).resolve().parents[1]
MANUAL_DATA_PATH = BASE_PATH / "manual_data"
URL_RE = re.compile(r"https?://\S+")
BRACKETED_URL_RE = re.compile(r"[（(]\s*https?://[^\s)）]+[)）]?")
WHITESPACE_RE = re.compile(r"\s+")
INLINE_CLAUSE_SPLIT_RE = re.compile(r"\s+/\s+")
ROLE_SPLIT_RE = re.compile(r"\s*(?:・|/|／|&|＆|\band\b|、|,)\s*", re.IGNORECASE)
CONTRIBUTOR_SPLIT_RE = re.compile(r"\s*(?:/|／|,|、|・|&|＆|\band\b)\s*", re.IGNORECASE)
SKIP_ROLE_LABELS = {
    "公式サイト",
    "公式X",
    "公式 X",
    "公式Twitter",
    "劇場版公式サイト",
    "作詞",
    "作曲",
    "作詞・作曲",
    "作詞・作曲・編曲",
    "編曲",
    "Lyrics & Music",
    "Arrangement",
    "Music",
    "原曲",
    "原作",
    "バーチャル・シンガーver.",
    "◆バーチャル・シンガーver.",
}


def _load_alias_file(path: Path, default_value: Dict[str, str]) -> Dict[str, str]:
    if not path.exists():
        return dict(default_value)

    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)

    merged = dict(default_value)
    if isinstance(payload, dict):
        merged.update({str(key): str(value) for key, value in payload.items()})
    return merged


@lru_cache(maxsize=1)
def load_role_aliases() -> Dict[str, str]:
    return _load_alias_file(MANUAL_DATA_PATH / "staff_role_aliases.json", DEFAULT_ROLE_ALIASES)


@lru_cache(maxsize=1)
def load_name_aliases() -> Dict[str, str]:
    return _load_alias_file(MANUAL_DATA_PATH / "staff_name_aliases.json", DEFAULT_NAME_ALIASES)


def normalize_role_label(role_raw: str) -> str:
    normalized = _clean_token(role_raw)
    if not normalized:
        return "unknown"

    role_aliases = load_role_aliases()
    if normalized in role_aliases:
        return role_aliases[normalized]

    normalized_casefold = normalized.casefold()
    for alias, canonical_role in role_aliases.items():
        if alias.casefold() == normalized_casefold:
            return canonical_role

    return "unknown"


def normalize_staff_name(name_raw: str) -> str:
    cleaned = _clean_name_text(name_raw)
    if not cleaned:
        return ""
    return load_name_aliases().get(cleaned, cleaned)


def _clean_token(value: str) -> str:
    return WHITESPACE_RE.sub(" ", value.replace("\u3000", " ")).strip(" \t\r\n:-")


def _strip_dangling_opening_brackets(value: str) -> str:
    cleaned = value
    while cleaned.endswith(("(", "（")):
        cleaned = cleaned[:-1].rstrip()
    return cleaned


def _clean_name_text(value: str) -> str:
    without_bracketed_urls = BRACKETED_URL_RE.sub("", value)
    without_urls = URL_RE.sub("", without_bracketed_urls)
    without_handles = re.sub(r"\(\s*https?://[^)]*\)", "", without_urls)
    return _strip_dangling_opening_brackets(_clean_token(without_handles))


def _is_obviously_not_staff_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return True
    if stripped.startswith("http://") or stripped.startswith("https://"):
        return True
    return False


def _split_inline_clauses(line: str) -> List[str]:
    segments = [segment.strip() for segment in INLINE_CLAUSE_SPLIT_RE.split(line) if segment.strip()]
    if len(segments) <= 1:
        return [line]

    if all(("：" in segment or ":" in segment or re.search(r"\bby\b", segment, re.IGNORECASE)) for segment in segments):
        return segments

    return [line]


def _split_role_and_contributor(line: str) -> Tuple[str, str] | None:
    by_match = re.match(r"^(?P<role>.+?)\s+by\s+(?P<name>.+)$", line, re.IGNORECASE)
    if by_match:
        return by_match.group("role"), by_match.group("name")

    first_url_match = URL_RE.search(line)
    first_url_start = first_url_match.start() if first_url_match else len(line) + 1

    if "：" in line:
        delimiter_index = line.index("：")
        if delimiter_index < first_url_start:
            role_raw, contributor_raw = line.split("：", 1)
            return role_raw, contributor_raw
    if ":" in line:
        delimiter_index = line.index(":")
        if delimiter_index < first_url_start:
            role_raw, contributor_raw = line.split(":", 1)
            return role_raw, contributor_raw

    return None


def _split_role_labels(role_raw: str) -> List[str]:
    cleaned_role = _clean_token(role_raw)
    if not cleaned_role:
        return []

    if normalize_role_label(cleaned_role) != "unknown":
        return [cleaned_role]

    role_parts = [_clean_token(part) for part in ROLE_SPLIT_RE.split(cleaned_role) if _clean_token(part)]
    return role_parts or [cleaned_role]


def _split_contributor_names(contributor_raw: str) -> List[str]:
    cleaned_text = _clean_name_text(contributor_raw)
    if not cleaned_text:
        return []

    contributors = [_clean_name_text(part) for part in CONTRIBUTOR_SPLIT_RE.split(cleaned_text)]
    return [item for item in contributors if item]


def parse_staff_lines(description: str) -> Dict[str, List[Dict[str, str]]]:
    result = {
        "contributors": [],
        "unparsedLines": [],
        "unknownRoleLines": [],
    }
    seen_contributors = set()
    unknown_lines_seen = set()

    for raw_line in description.splitlines():
        line = raw_line.strip()
        if _is_obviously_not_staff_line(line):
            continue

        parsed_any_clause = False
        skipped_clause = False
        for clause in _split_inline_clauses(line):
            split_result = _split_role_and_contributor(clause)
            if split_result is None:
                continue

            role_raw, contributor_raw = split_result
            role_raw = _clean_token(role_raw)
            if not role_raw or role_raw in SKIP_ROLE_LABELS:
                skipped_clause = True
                continue

            role_labels = _split_role_labels(role_raw)
            contributor_names = _split_contributor_names(contributor_raw)
            if not role_labels or not contributor_names:
                continue

            parsed_any_clause = True
            for role_label in role_labels:
                normalized_role = normalize_role_label(role_label)
                for contributor_name in contributor_names:
                    normalized_name = normalize_staff_name(contributor_name)
                    if not normalized_name:
                        continue

                    dedupe_key = (normalized_role, normalized_name, line)
                    if dedupe_key in seen_contributors:
                        continue
                    seen_contributors.add(dedupe_key)

                    contributor = {
                        "name": normalized_name,
                        "nameRaw": contributor_name,
                        "role": normalized_role,
                        "roleRaw": role_label,
                        "sourceLine": line,
                    }
                    result["contributors"].append(contributor)

                    if normalized_role == "unknown" and line not in unknown_lines_seen:
                        result["unknownRoleLines"].append(line)
                        unknown_lines_seen.add(line)

        if not parsed_any_clause and not skipped_clause and ("：" in line or ":" in line or re.search(r"\bby\b", line, re.IGNORECASE)):
            result["unparsedLines"].append(line)

    return result


def _dedupe_names(names: List[str]) -> List[str]:
    seen = set()
    result = []
    for name in names:
        if name in seen:
            continue
        seen.add(name)
        result.append(name)
    return result


def _dedupe_contributors(contributors: List[Dict[str, str]]) -> List[Dict[str, str]]:
    seen = set()
    result = []
    for contributor in contributors:
        dedupe_key = (
            contributor.get("role"),
            contributor.get("name"),
            contributor.get("roleRaw"),
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)
        result.append(contributor)
    return result


def build_video_staff(description: str) -> Dict[str, object]:
    parsed = parse_staff_lines(description)
    contributors = parsed["contributors"]
    other_role_keys = ("illustrationAnimation", "lyricDesign", "animation", "design", "cg3d", "unknown")

    staff = {
        "illustrators": [],
        "pvCreators": [],
        "otherRoles": {role_key: [] for role_key in other_role_keys},
        "contributors": contributors,
        "unparsedLines": parsed["unparsedLines"],
        "unknownRoleLines": parsed["unknownRoleLines"],
    }

    for contributor in contributors:
        role = contributor["role"]
        name = contributor["name"]
        if role == "illustrator":
            staff["illustrators"].append(name)
        elif role == "pvCreator":
            staff["pvCreators"].append(name)
        elif role in staff["otherRoles"]:
            staff["otherRoles"][role].append(name)

    staff["illustrators"] = _dedupe_names(staff["illustrators"])
    staff["pvCreators"] = _dedupe_names(staff["pvCreators"])
    for role_key in other_role_keys:
        staff["otherRoles"][role_key] = _dedupe_names(staff["otherRoles"][role_key])

    return staff


def summarize_song_staff(video_staff_list: List[Dict[str, object]]) -> Dict[str, object]:
    other_role_keys = ("illustrationAnimation", "lyricDesign", "animation", "design", "cg3d", "unknown")
    summary = {
        "illustrators": [],
        "pvCreators": [],
        "otherRoles": {role_key: [] for role_key in other_role_keys},
        "allContributors": [],
    }

    for video_staff in video_staff_list:
        summary["illustrators"].extend(video_staff.get("illustrators", []))
        summary["pvCreators"].extend(video_staff.get("pvCreators", []))

        other_roles = video_staff.get("otherRoles", {})
        for role_key in other_role_keys:
            summary["otherRoles"][role_key].extend(other_roles.get(role_key, []))

        summary["allContributors"].extend(video_staff.get("contributors", []))

    summary["illustrators"] = _dedupe_names(summary["illustrators"])
    summary["pvCreators"] = _dedupe_names(summary["pvCreators"])
    for role_key in other_role_keys:
        summary["otherRoles"][role_key] = _dedupe_names(summary["otherRoles"][role_key])
    summary["allContributors"] = _dedupe_contributors(summary["allContributors"])

    return summary


def build_staff_index_rows(songs: List[Dict[str, object]]) -> List[Dict[str, str]]:
    rows = []
    for song in songs:
        for video in song.get("videos", []):
            staff = video.get("staff", {})
            for contributor in staff.get("contributors", []):
                rows.append(
                    {
                        "songId": song.get("id"),
                        "songTitle": song.get("title"),
                        "videoId": video.get("videoId"),
                        "videoTitle": video.get("title"),
                        "name": contributor.get("name"),
                        "role": contributor.get("role"),
                        "roleRaw": contributor.get("roleRaw"),
                    }
                )
    return rows


def build_staff_review_rows(songs: List[Dict[str, object]]) -> List[Dict[str, object]]:
    rows = []
    for song in songs:
        for video in song.get("videos", []):
            staff = video.get("staff", {})
            unknown_role_lines = staff.get("unknownRoleLines", [])
            unparsed_lines = staff.get("unparsedLines", [])
            if not unknown_role_lines and not unparsed_lines:
                continue

            rows.append(
                {
                    "songId": song.get("id"),
                    "songTitle": song.get("title"),
                    "videoId": video.get("videoId"),
                    "videoTitle": video.get("title"),
                    "unknownRoleLines": unknown_role_lines,
                    "unparsedLines": unparsed_lines,
                }
            )
    return rows
