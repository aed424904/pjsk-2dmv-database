"""Helpers for extracting performer credits from loosely structured video metadata."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional


URL_RE = re.compile(r"https?://\S+")
WHITESPACE_RE = re.compile(r"\s+")
BRACKETED_URL_RE = re.compile(r"[（(]\s*https?://[^\s)）]+[)）]?")
LEADING_BULLET_RE = re.compile(r"^[■▼▽◆□☻●◎○・]+")
PERFORMER_SPLIT_RE = re.compile(r"\s*(?:/|／|,|、|・|&|＆|×|\band\b)\s*", re.IGNORECASE)
TITLE_FEAT_RE = re.compile(r"\b(?:feat|ft)\.?\s*(.+)$", re.IGNORECASE)
TITLE_WITH_RE = re.compile(r"\bwith\s+(.+)$", re.IGNORECASE)
DESCRIPTION_FEAT_RE = re.compile(r"^(?:feat\.?|ft\.?|featuring)\s*(.+)$", re.IGNORECASE)
LABELED_PERFORMER_RE = re.compile(
    r"^[■▼▽◆□☻●◎○・\s-]*(?:main\s+vocal(?:\s*&\s*chorus)?s?|vocals?|vocaloid(?:\s*edit)?|vo\.?|singer|歌|歌唱|うた)\s*(?:[：:]|[／/、,]|\s)+\s*(.+)$",
    re.IGNORECASE,
)
TRAILING_BRACKET_RE = re.compile(r"\s*[（(【\[](?P<inner>[^)\]】）]+)[)】\]]\s*$")

NOISE_MARKERS = {
    "music",
    "lyrics",
    "lyric",
    "movie",
    "video",
    "illustration",
    "illust",
    "animation",
    "arrange",
    "arranger",
    "mix",
    "mastering",
    "inst",
    "off vocal",
    "作詞",
    "作曲",
    "編曲",
    "動画",
    "映像",
    "イラスト",
    "絵",
    "vocaloid",
    "vocaloids",
    "official",
    "mv",
    "lyric video",
    "ver",
}

ROLE_ONLY_MARKERS = {
    "作詞",
    "作曲",
    "編曲",
    "lyrics",
    "music",
    "arrangement",
    "arrange",
    "composer",
    "lyricist",
}

DEFAULT_CRYPTON_VOCALOIDS = ["初音ミク", "鏡音リン", "鏡音レン", "巡音ルカ", "KAITO", "MEIKO"]

PERFORMER_ALIAS_MAP = {
    "初音ミク": "初音ミク",
    "hatsunemiku": "初音ミク",
    "miku": "初音ミク",
    "鏡音リン": "鏡音リン",
    "kagaminerin": "鏡音リン",
    "rin": "鏡音リン",
    "鏡音レン": "鏡音レン",
    "kagaminalen": "鏡音レン",
    "kagaminelen": "鏡音レン",
    "len": "鏡音レン",
    "巡音ルカ": "巡音ルカ",
    "megurineluka": "巡音ルカ",
    "luka": "巡音ルカ",
    "meiko": "MEIKO",
    "kaito": "KAITO",
    "flower": "flower",
    "vflower": "flower",
    "flowerr": "flower",
    "重音テト": "重音テト",
    "重音テトsv": "重音テト",
    "kasaneteto": "重音テト",
    "teto": "重音テト",
    "可不": "可不",
    "kafu": "可不",
}


def _clean_token(value: str) -> str:
    return WHITESPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip(" \t\r\n:-")


def _strip_dangling_opening_brackets(value: str) -> str:
    cleaned = value
    while cleaned.endswith(("(", "（")):
        cleaned = cleaned[:-1].rstrip()
    return cleaned


def _canonicalize_performer_name(value: str) -> str:
    key = re.sub(r"[\s._-]+", "", value.casefold())
    return PERFORMER_ALIAS_MAP.get(key, value)


def extract_known_performers_from_text(value: str) -> List[str]:
    compact = re.sub(r"[\s._-]+", "", str(value or "").casefold())
    performers = []
    seen = set()

    for alias, canonical in PERFORMER_ALIAS_MAP.items():
        alias_key = re.sub(r"[\s._-]+", "", alias.casefold())
        if alias_key in compact and canonical not in seen:
            seen.add(canonical)
            performers.append(canonical)

    return performers


def _strip_trailing_nonperformer_annotation(value: str) -> str:
    cleaned = value
    while True:
        match = TRAILING_BRACKET_RE.search(cleaned)
        if not match:
            return cleaned
        inner = match.group("inner")
        if extract_known_performers_from_text(inner):
            return cleaned
        cleaned = cleaned[:match.start()].rstrip()


def _is_performer_label_only_line(value: str) -> bool:
    cleaned = LEADING_BULLET_RE.sub("", str(value or "")).strip()
    if not cleaned:
        return False

    parts = [part.strip() for part in re.split(r"[／/&＆・,、]+", cleaned.replace(":", "").replace("：", "")) if part.strip()]
    if not parts:
        return False

    saw_performer_label = False
    for part in parts:
        lowered = part.casefold()
        if re.fullmatch(r"(?:main\s+vocal(?:\s*&\s*chorus)?s?|vocals?|vocaloid(?:\s*edit)?|vo\.?|singer|歌|歌唱|うた)", part, re.IGNORECASE):
            saw_performer_label = True
            continue
        if lowered in ROLE_ONLY_MARKERS or part in ROLE_ONLY_MARKERS:
            continue
        return False

    return saw_performer_label


def extract_performers_from_text(value: str) -> List[str]:
    performers = split_performer_names(value)
    if performers:
        return performers
    return extract_known_performers_from_text(value)


def extract_group_performers_from_title(title: str) -> List[str]:
    lowered = str(title or "").casefold()
    if "vocaloids" in lowered or "ボカロ6人" in title:
        return list(DEFAULT_CRYPTON_VOCALOIDS)
    return []


def normalize_performer_name(value: str) -> str:
    without_bracketed_urls = BRACKETED_URL_RE.sub("", value)
    without_urls = URL_RE.sub("", without_bracketed_urls)
    without_handles = re.sub(r"@\S+", "", without_urls)
    without_hashes = without_handles.replace("#", "")
    without_bullets = LEADING_BULLET_RE.sub("", without_hashes)
    without_label = re.sub(
        r"^(?:main\s+vocal(?:\s*&\s*chorus)?|vocal(?:oid)?(?:\s*edit)?|vo\.?|singer|歌|歌唱|うた)\s*(?:[：:]|[／/、,]|\s)+\s*",
        "",
        without_bullets,
        flags=re.IGNORECASE,
    )
    without_honorifics = re.sub(r"(?:さん)\s*$", "", without_label)
    without_annotation = _strip_trailing_nonperformer_annotation(without_honorifics)
    cleaned = _strip_dangling_opening_brackets(_clean_token(without_annotation).strip("[]()（）「」『』【】'\""))
    return _canonicalize_performer_name(cleaned)


def split_performer_names(value: str) -> List[str]:
    normalized = normalize_performer_name(value)
    if not normalized:
        return []

    names = []
    seen = set()
    for item in PERFORMER_SPLIT_RE.split(normalized):
        name = normalize_performer_name(item)
        if not name:
            continue
        lowered = name.casefold()
        if lowered in NOISE_MARKERS or lowered.startswith("http"):
            continue
        if name in seen:
            continue
        seen.add(name)
        names.append(name)
    return names


def _build_result(
    performers: Optional[List[str]] = None,
    source: str = "none",
    confidence: str = "low",
    matched_text: str = "",
    needs_review: bool = True,
) -> Dict[str, Any]:
    return {
        "performers": performers or [],
        "source": source,
        "confidence": confidence,
        "matchedText": matched_text,
        "needsReview": needs_review,
    }


def _extract_from_description(description: str) -> Optional[Dict[str, Any]]:
    lines = [line.strip() for line in description.splitlines() if line.strip()]
    for index, raw_line in enumerate(lines):
        line = raw_line.strip()
        if not line or line.startswith("http://") or line.startswith("https://"):
            continue

        labeled_match = LABELED_PERFORMER_RE.match(line)
        if labeled_match:
            performers = extract_performers_from_text(labeled_match.group(1))
            if performers:
                return _build_result(
                    performers=performers,
                    source="description_label",
                    confidence="high",
                    matched_text=line,
                    needs_review=False,
                )

        if _is_performer_label_only_line(line) and index + 1 < len(lines):
            next_line = lines[index + 1]
            if not next_line.startswith("http://") and not next_line.startswith("https://"):
                performers = extract_performers_from_text(next_line)
                if performers:
                    return _build_result(
                        performers=performers,
                        source="description_next_line",
                        confidence="high",
                        matched_text=f"{line} -> {next_line}",
                        needs_review=False,
                    )

        feat_match = DESCRIPTION_FEAT_RE.match(line)
        if feat_match:
            performers = extract_performers_from_text(feat_match.group(1))
            if performers:
                return _build_result(
                    performers=performers,
                    source="description_feat",
                    confidence="high",
                    matched_text=line,
                    needs_review=False,
                )

    return None


def _extract_from_title(title: str) -> Optional[Dict[str, Any]]:
    feat_match = TITLE_FEAT_RE.search(title)
    if feat_match:
        performers = extract_performers_from_text(feat_match.group(1))
        if performers:
            return _build_result(
                performers=performers,
                source="title_feat",
                confidence="high",
                matched_text=feat_match.group(0),
                needs_review=False,
            )

    with_match = TITLE_WITH_RE.search(title)
    if with_match:
        performers = extract_performers_from_text(with_match.group(1))
        if performers:
            return _build_result(
                performers=performers,
                source="title_with",
                confidence="high",
                matched_text=with_match.group(0),
                needs_review=False,
            )

    for separator in ("／", "/", "｜", "|"):
        if separator not in title:
            continue
        suffix = title.rsplit(separator, 1)[1].strip()
        performers = extract_performers_from_text(suffix)
        if performers:
            return _build_result(
                performers=performers,
                source="title_separator",
                confidence="medium",
                matched_text=suffix,
                needs_review=False,
            )

    keyword_performers = extract_known_performers_from_text(title)
    if keyword_performers:
        return _build_result(
            performers=keyword_performers,
            source="title_keyword",
            confidence="medium",
            matched_text=title,
            needs_review=False,
        )

    group_performers = extract_group_performers_from_title(title)
    if group_performers:
        return _build_result(
            performers=group_performers,
            source="title_group",
            confidence="medium",
            matched_text=title,
            needs_review=False,
        )

    return None


def extract_video_performers(
    title: str,
    description: str,
    manual_performers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    if manual_performers:
        performers = split_performer_names(" / ".join(manual_performers))
        if performers:
            return _build_result(
                performers=performers,
                source="manual",
                confidence="high",
                matched_text=" / ".join(manual_performers),
                needs_review=False,
            )

    from_description = _extract_from_description(description or "")
    if from_description:
        return from_description

    from_title = _extract_from_title(title or "")
    if from_title:
        return from_title

    return _build_result()


def summarize_song_performers(video_entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    performers: List[str] = []
    seen = set()

    for video in video_entries:
        extraction = video.get("performerExtraction", {})
        for performer in extraction.get("performers", []):
            if performer in seen:
                continue
            seen.add(performer)
            performers.append(performer)

    return {
        "performers": performers,
    }


def build_performer_review_rows(songs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = []

    for song in songs:
        for video in song.get("videos", []):
            extraction = video.get("performerExtraction", {})
            if not extraction or not extraction.get("needsReview"):
                continue

            rows.append(
                {
                    "songId": song.get("id"),
                    "songTitle": song.get("title"),
                    "videoId": video.get("videoId"),
                    "videoTitle": video.get("title"),
                    "sourceKey": video.get("sourceKey"),
                    "sourceName": video.get("sourceName"),
                    "performers": extraction.get("performers", []),
                    "confidence": extraction.get("confidence"),
                    "matchedText": extraction.get("matchedText"),
                    "descriptionPreview": " | ".join(
                        [line.strip() for line in str(video.get("description") or "").splitlines() if line.strip()][:6]
                    ),
                }
            )

    return rows
