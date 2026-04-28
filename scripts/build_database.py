#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Sekai 2DMV Database Builder
将多个数据源整合成统一的数据库
"""

import json
import os
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import re

try:
    from .staff_extraction import build_staff_index_rows
    from .staff_extraction import build_staff_review_rows
    from .staff_extraction import build_video_staff
    from .staff_extraction import summarize_song_staff
    from .sync_aliases import sync_aliases
    from .video_credit_extraction import build_performer_review_rows
    from .video_credit_extraction import extract_video_performers
    from .video_credit_extraction import summarize_song_performers
    from .video_source_registry import get_preferred_source_snapshots
    from .video_source_registry import load_video_sources
except ImportError:
    from staff_extraction import build_staff_index_rows
    from staff_extraction import build_staff_review_rows
    from staff_extraction import build_video_staff
    from staff_extraction import summarize_song_staff
    from sync_aliases import sync_aliases
    from video_credit_extraction import build_performer_review_rows
    from video_credit_extraction import extract_video_performers
    from video_credit_extraction import summarize_song_performers
    from video_source_registry import get_preferred_source_snapshots
    from video_source_registry import load_video_sources

class DatabaseBuilder:
    OFFICIAL_CHANNEL_TITLE = "プロジェクトセカイ カラフルステージ! feat. 初音ミク"
    OFFICIAL_CHANNEL_ID = "UCdMGYXL38w6htx6Yf9YJa-w"
    VERSION_BASE_LABELS = {
        'original': '本家',
        'sekai': 'SEKAI ver',
        'virtual_singer': 'Virtual Singer ver',
        'another_vocal': 'Another Vocal',
        'unknown': '未分类',
    }
    VERSION_SPECIAL_LABELS = {
        'april_fool': '愚人节版',
    }
    VERSION_BASE_ORDER = ['sekai', 'virtual_singer', 'another_vocal', 'original', 'unknown']
    VERSION_SPECIAL_ORDER = ['april_fool']
    UNIT_VERSION_MARKERS = [
        'Leo/need',
        'MORE MORE JUMP',
        'MORE MORE JUMP！',
        'Vivid BAD SQUAD',
        'ワンダーランズ×ショウタイム',
        'ワンダーランズ x ショウタイム',
        'ワンダショ',
        '25時、ナイトコードで。',
        '25時、ナイトコードで',
        '25-ji, Nightcord de.',
    ]
    VIRTUAL_SINGER_MARKERS = [
        'バーチャル・シンガー',
        'virtual singer',
        'virtual singer ver',
        'virtual singer version',
    ]
    VIRTUAL_SINGER_NAMES = [
        '初音ミク',
        '鏡音リン',
        '鏡音レン',
        '巡音ルカ',
        'MEIKO',
        'KAITO',
    ]
    ANOTHER_VOCAL_MARKERS = [
        'アナザーボーカル',
        'another vocal',
        'another vocal ver',
        'another vocal version',
    ]
    SEKAI_VERSION_MARKERS = [
        'セカイver',
        'セカイ ver',
        'sekai ver',
        'sekai version',
    ]
    ORIGINAL_VERSION_MARKERS = [
        '本家',
        '原曲',
        'original ver',
        'original version',
        'オリジナル',
    ]
    APRIL_FOOL_MARKERS = [
        'エイプリルフール',
        'april fool',
        '愚人节',
    ]

    def __init__(self, base_path: str):
        self.base_path = Path(base_path)
        self.youtube_data = None
        self.youtube_source_name = None
        self.youtube_source_names: List[str] = []
        self.video_sources: List[Dict[str, Any]] = []
        self.manual_videos = []
        self.original_video_overrides: Dict[str, Dict[str, Any]] = {}
        self.sekai_musics = []
        self.sekai_music_tags = []
        self.sekai_units = []
        self.base_musics = []
        self.base_music_source = None
        self.aliases = {}
        self.corrections = {}

        # 输出统计
        self.stats = {
            'total_songs': 0,
            'total_videos': 0,
            'matched_sekai': 0,
            'unmatched_videos': [],
            'video_type_breakdown': {},
            'unit_breakdown': {}
        }

    def extract_video_id_from_url(self, url: str) -> Optional[str]:
        """从常见的 YouTube 链接中提取 videoId。"""
        if not url:
            return None

        patterns = [
            r"[?&]v=([A-Za-z0-9_-]{11})",
            r"youtu\.be/([A-Za-z0-9_-]{11})",
            r"youtube\.com/embed/([A-Za-z0-9_-]{11})",
            r"youtube\.com/shorts/([A-Za-z0-9_-]{11})",
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def build_youtube_thumbnails(self, video_id: str) -> Dict[str, str]:
        """根据 videoId 生成标准 YouTube 缩略图。"""
        return {
            'default': f'https://i.ytimg.com/vi/{video_id}/default.jpg',
            'medium': f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg',
            'high': f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg',
            'standard': f'https://i.ytimg.com/vi/{video_id}/sddefault.jpg',
            'maxres': f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg',
        }

    def normalize_string_list(self, values: Any) -> List[str]:
        if not values:
            return []

        if isinstance(values, str):
            raw_values = [values]
        elif isinstance(values, list):
            raw_values = values
        else:
            return []

        normalized = []
        for value in raw_values:
            cleaned = str(value or '').strip()
            if cleaned:
                normalized.append(cleaned)
        return normalized

    def normalize_extractors(self, extractors: Any) -> List[str]:
        normalized = []
        seen = set()

        for extractor in self.normalize_string_list(extractors):
            key = extractor.strip().lower()
            if not key or key in seen:
                continue
            seen.add(key)
            normalized.append(key)

        return normalized

    def normalize_manual_video(self, video: Dict[str, Any], fallback_position: int) -> Optional[Dict[str, Any]]:
        """将手动补录条目标准化成播放列表视频结构。"""
        if not isinstance(video, dict):
            return None

        url = str(video.get('url') or '').strip()
        video_id = str(video.get('videoId') or self.extract_video_id_from_url(url) or '').strip()
        title = str(video.get('title') or '').strip()
        song_title = str(video.get('songTitle') or '').strip()
        published_at = str(video.get('publishedAt') or '').strip()

        if not song_title and title:
            song_title = self.extract_song_title(title)

        if not video_id:
            print(f"[WARN] 跳过手动视频：缺少 videoId/url ({song_title or title or '未命名条目'})")
            return None
        if not title:
            print(f"[WARN] 跳过手动视频：缺少 title ({video_id})")
            return None
        if not song_title:
            print(f"[WARN] 跳过手动视频：缺少 songTitle ({video_id})")
            return None
        if not published_at:
            print(f"[WARN] 跳过手动视频：缺少 publishedAt ({video_id})")
            return None

        if not url:
            url = f'https://www.youtube.com/watch?v={video_id}'

        thumbnails = video.get('thumbnails')
        if not isinstance(thumbnails, dict) or not thumbnails:
            thumbnails = self.build_youtube_thumbnails(video_id)

        try:
            position = int(video.get('position'))
        except (TypeError, ValueError):
            position = fallback_position

        return {
            'videoId': video_id,
            'url': url,
            'title': title,
            'songTitle': song_title,
            'description': str(video.get('description') or ''),
            'channelTitle': str(video.get('channelTitle') or self.OFFICIAL_CHANNEL_TITLE),
            'channelId': str(video.get('channelId') or self.OFFICIAL_CHANNEL_ID),
            'publishedAt': published_at,
            'thumbnails': thumbnails,
            'position': position,
            'source': 'manual',
            'sourceKey': str(video.get('sourceKey') or 'manual'),
            'sourceName': str(video.get('sourceName') or 'Manual Entry'),
            'sourceKind': str(video.get('sourceKind') or 'manual'),
            'sourceUrl': str(video.get('sourceUrl') or ''),
            'notes': str(video.get('notes') or ''),
            'version': video.get('version'),
            'versionBase': video.get('versionBase'),
            'versionSpecial': video.get('versionSpecial'),
            'videoType': video.get('videoType'),
            'extractors': self.normalize_extractors(video.get('extractors')),
            'performers': self.normalize_string_list(video.get('performers')),
        }

    def load_manual_videos(self) -> List[Dict[str, Any]]:
        """加载手动补录视频。支持 {"videos": [...]} 或直接数组。"""
        manual_videos_path = self.base_path / "manual_data" / "manual_videos.json"
        if not manual_videos_path.exists():
            return []

        with open(manual_videos_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        if isinstance(payload, dict):
            raw_videos = payload.get('videos', [])
        elif isinstance(payload, list):
            raw_videos = payload
        else:
            raise ValueError(f"manual_videos.json 格式错误: {manual_videos_path}")

        normalized_videos = []
        for index, video in enumerate(raw_videos):
            normalized = self.normalize_manual_video(video, fallback_position=10_000 + index)
            if normalized:
                normalized_videos.append(normalized)

        print(f"[OK] 手动补录视频: {len(normalized_videos)} 条")
        return normalized_videos

    def normalize_video_override(self, video_id: str, override: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        if not video_id or not isinstance(override, dict):
            return None

        normalized: Dict[str, Any] = {}

        for key in ('title', 'songTitle', 'description', 'notes', 'videoType'):
            if key in override:
                normalized[key] = override.get(key)

        if 'version' in override:
            normalized['version'] = override.get('version')
        if 'versionBase' in override:
            normalized['versionBase'] = override.get('versionBase')
        if 'versionSpecial' in override:
            normalized['versionSpecial'] = override.get('versionSpecial')

        if 'performers' in override:
            normalized['performers'] = self.normalize_string_list(override.get('performers'))

        if 'extractors' in override:
            normalized['extractors'] = self.normalize_extractors(override.get('extractors'))

        if normalized.get('performers') and 'performers' not in normalized.get('extractors', []):
            normalized.setdefault('extractors', [])
            normalized['extractors'].append('performers')

        return normalized or None

    def load_original_video_overrides(self) -> Dict[str, Dict[str, Any]]:
        overrides_path = self.base_path / "manual_data" / "original_video_overrides.json"
        if not overrides_path.exists():
            return {}

        with open(overrides_path, 'r', encoding='utf-8') as f:
            payload = json.load(f)

        if isinstance(payload, dict):
            raw_overrides = payload.get('videos', payload)
        elif isinstance(payload, list):
            raw_overrides = payload
        else:
            raise ValueError(f"original_video_overrides.json 格式错误: {overrides_path}")

        normalized_overrides: Dict[str, Dict[str, Any]] = {}

        if isinstance(raw_overrides, dict):
            for raw_video_id, raw_override in raw_overrides.items():
                video_id = str(raw_video_id or '').strip()
                normalized = self.normalize_video_override(video_id, raw_override)
                if normalized:
                    normalized_overrides[video_id] = normalized
        elif isinstance(raw_overrides, list):
            for raw_override in raw_overrides:
                if not isinstance(raw_override, dict):
                    continue
                video_id = str(raw_override.get('videoId') or '').strip()
                normalized = self.normalize_video_override(video_id, raw_override)
                if normalized:
                    normalized_overrides[video_id] = normalized
        else:
            raise ValueError(f"original_video_overrides.json 格式错误: {overrides_path}")

        print(f"[OK] 原曲视频覆写: {len(normalized_overrides)} 条")
        return normalized_overrides

    def apply_original_video_override(self, video: Dict[str, Any]) -> Dict[str, Any]:
        video_id = str(video.get('videoId') or '').strip()
        raw_override = self.original_video_overrides.get(video_id)
        override = self.normalize_video_override(video_id, raw_override) if raw_override else None
        if not override:
            return video

        merged = dict(video)

        for key in ('title', 'songTitle', 'description', 'notes', 'videoType', 'version', 'versionBase', 'versionSpecial'):
            if key in override:
                merged[key] = override[key]

        if 'performers' in override:
            merged['performers'] = self.normalize_string_list(override.get('performers'))

        base_extractors = self.normalize_extractors(video.get('extractors'))
        override_extractors = self.normalize_extractors(override.get('extractors'))
        if base_extractors or override_extractors:
            merged['extractors'] = self.normalize_extractors(base_extractors + override_extractors)

        return merged

    def merge_video_sources(
        self,
        playlist_videos: List[Dict[str, Any]],
        manual_videos: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """合并播放列表与手动补录，手动视频按 videoId 去重。"""
        merged = list(playlist_videos)
        existing_ids = {video.get('videoId') for video in playlist_videos if video.get('videoId')}
        skipped_duplicates = 0

        for manual_video in manual_videos:
            video_id = manual_video.get('videoId')
            if video_id and video_id in existing_ids:
                skipped_duplicates += 1
                continue
            if video_id:
                existing_ids.add(video_id)
            merged.append(manual_video)

        if skipped_duplicates:
            print(f"[WARN] 跳过重复手动视频 {skipped_duplicates} 条（videoId 已存在于播放列表）")

        return merged

    def score_source_video(self, video: Dict[str, Any]) -> int:
        score = 0
        if video.get('description'):
            score += len(str(video.get('description')))
        if video.get('publishedAt'):
            score += 32
        if video.get('songTitle'):
            score += 24
        if video.get('channelTitle'):
            score += 12
        if video.get('version') or video.get('versionBase'):
            score += 16
        if video.get('videoType'):
            score += 8
        return score

    def normalize_playlist_video(
        self,
        video: Dict[str, Any],
        source: Dict[str, Any],
        payload_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(video, dict):
            return None

        payload_metadata = payload_metadata or {}
        video_id = str(video.get('videoId') or '').strip()
        title = str(video.get('title') or '').strip()
        if not video_id or not title:
            return None

        url = str(video.get('url') or '').strip()
        if not url:
            url = f'https://www.youtube.com/watch?v={video_id}'

        thumbnails = video.get('thumbnails')
        if not isinstance(thumbnails, dict) or not thumbnails:
            thumbnails = self.build_youtube_thumbnails(video_id)

        try:
            position = int(video.get('position'))
        except (TypeError, ValueError):
            position = 0

        normalized = {
            'videoId': video_id,
            'url': url,
            'title': title,
            'songTitle': str(video.get('songTitle') or '').strip(),
            'description': str(video.get('description') or ''),
            'channelTitle': str(video.get('channelTitle') or ''),
            'channelId': str(video.get('channelId') or ''),
            'publishedAt': str(video.get('publishedAt') or ''),
            'thumbnails': thumbnails,
            'position': position,
            'source': str(video.get('source') or f"playlist:{source['key']}"),
            'sourceKey': str(video.get('sourceKey') or payload_metadata.get('sourceKey') or source['key']),
            'sourceName': str(video.get('sourceName') or payload_metadata.get('sourceName') or source['name']),
            'sourceKind': str(video.get('sourceKind') or payload_metadata.get('sourceKind') or source['kind']),
            'sourceUrl': str(video.get('sourceUrl') or payload_metadata.get('sourceUrl') or source.get('url') or ''),
            'notes': str(video.get('notes') or ''),
            'version': video.get('version'),
            'versionBase': video.get('versionBase') or payload_metadata.get('versionBase') or source.get('versionBase'),
            'versionSpecial': video.get('versionSpecial') or payload_metadata.get('versionSpecial') or source.get('versionSpecial'),
            'videoType': video.get('videoType') or payload_metadata.get('videoType') or source.get('videoType'),
            'extractors': self.normalize_extractors(
                video.get('extractors') or payload_metadata.get('extractors') or source.get('extractors')
            ),
            'performers': self.normalize_string_list(video.get('performers')),
        }
        return normalized

    def merge_playlist_snapshots(self, playlist_videos: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        merged_by_id: Dict[str, Dict[str, Any]] = {}
        ordered_ids: List[str] = []
        skipped_duplicates = 0

        for video in playlist_videos:
            video_id = video.get('videoId')
            if not video_id:
                continue

            if video_id not in merged_by_id:
                merged_by_id[video_id] = video
                ordered_ids.append(video_id)
                continue

            skipped_duplicates += 1
            if self.score_source_video(video) > self.score_source_video(merged_by_id[video_id]):
                merged_by_id[video_id] = video

        if skipped_duplicates:
            print(f"[WARN] 检测到跨来源重复视频 {skipped_duplicates} 条，已按信息完整度保留更优条目")

        return [merged_by_id[video_id] for video_id in ordered_ids]

    def load_youtube_data_from_sources(self) -> Dict[str, Any]:
        self.video_sources = load_video_sources(self.base_path)
        preferred_sources = get_preferred_source_snapshots(self.base_path, self.video_sources)
        if not preferred_sources:
            raise FileNotFoundError(f"未找到可用的 YouTube 播放列表数据: {self.base_path / 'fetch_youtube_playlist'}")

        all_videos: List[Dict[str, Any]] = []
        self.youtube_source_names = []

        for source, snapshot_path in preferred_sources:
            with open(snapshot_path, 'r', encoding='utf-8') as f:
                payload = json.load(f)

            payload_metadata = payload.get('metadata', {}) if isinstance(payload, dict) else {}
            raw_videos = payload.get('videos', []) if isinstance(payload, dict) else []
            normalized_videos = []
            for raw_video in raw_videos:
                normalized = self.normalize_playlist_video(raw_video, source, payload_metadata)
                if normalized:
                    normalized_videos.append(normalized)

            all_videos.extend(normalized_videos)
            self.youtube_source_names.append(f"{source['name']} ({snapshot_path.name})")
            print(f"[OK] 视频来源加载完成: {source['name']} {len(normalized_videos)} 条 ({snapshot_path.name})")

        merged_videos = self.merge_playlist_snapshots(all_videos)
        return {
            'videos': merged_videos,
        }

    def load_data(self):
        """加载所有数据源"""
        print("[INFO] 正在加载数据源...")

        # 1. 加载 YouTube 数据
        self.youtube_data = self.load_youtube_data_from_sources()
        self.youtube_source_name = ', '.join(self.youtube_source_names)
        print(f"[OK] YouTube 数据加载完成: {len(self.youtube_data['videos'])} 个视频 ({len(self.youtube_source_names)} 个来源)")

        self.manual_videos = self.load_manual_videos()
        if self.manual_videos:
            self.youtube_data['videos'] = self.merge_video_sources(self.youtube_data['videos'], self.manual_videos)
            print(f"[OK] 合并后视频总数: {len(self.youtube_data['videos'])}")

        # 2. 加载 Sekai Viewer 数据
        sekai_path = self.base_path / "sekai viewer_json"

        with open(sekai_path / "musics.json", 'r', encoding='utf-8') as f:
            self.sekai_musics = json.load(f)
        print(f"[OK] Sekai 音乐数据: {len(self.sekai_musics)} 首歌曲")

        with open(sekai_path / "musicTag.json", 'r', encoding='utf-8') as f:
            self.sekai_music_tags = json.load(f)
        print(f"[OK] Sekai 标签数据: {len(self.sekai_music_tags)} 条记录")

        with open(sekai_path / "unitProfiles.json", 'r', encoding='utf-8') as f:
            self.sekai_units = json.load(f)
        print(f"[OK] Sekai 组合数据: {len(self.sekai_units)} 个组合")

        base_music_path = self.base_path / "output" / "musics_base.json"
        if base_music_path.exists():
            with open(base_music_path, 'r', encoding='utf-8') as f:
                base_music_payload = json.load(f)
            self.base_musics = base_music_payload.get('songs', [])
            self.base_music_source = "output/musics_base.json"
            print(f"[OK] 曲库基表数据: {len(self.base_musics)} 首歌曲")
        else:
            self.base_musics = []
            self.base_music_source = None
            print(f"[WARN] 未找到曲库基表: {base_music_path}")

        # 3. 加载手动维护数据
        manual_path = self.base_path / "manual_data"

        if (manual_path / "aliases.json").exists():
            with open(manual_path / "aliases.json", 'r', encoding='utf-8') as f:
                self.aliases = json.load(f)
            print(f"[OK] 别称数据: {len(self.aliases)} 首歌曲")

        if (manual_path / "corrections.json").exists():
            with open(manual_path / "corrections.json", 'r', encoding='utf-8') as f:
                self.corrections = json.load(f)
            print(f"[OK] 修正数据加载完成")

        self.original_video_overrides = self.load_original_video_overrides()

    def extract_song_title(self, video_title: str) -> str:
        """从视频标题中提取歌曲名"""
        # 示例: "幸福刑 / 25時、ナイトコードで。 × MEIKO" → "幸福刑"
        # 示例: "モザイクロール (Reloaded) / Leo/need × KAITO" → "モザイクロール"

        # 去除 (Reloaded) 等后缀
        title = re.sub(r'\s*\(.*?\)\s*', '', video_title)

        # 提取官方标题中 "/" 或 "／" 之前的歌曲名，兼容 "曲名/ 组合" 这种无空格格式
        if re.search(r'\s*[\/／]\s+', title):
            song_title = re.split(r'\s*[\/／]\s+', title, maxsplit=1)[0].strip()
        else:
            song_title = title.strip()

        # 应用修正
        if 'titleCorrections' in self.corrections:
            song_title = self.corrections['titleCorrections'].get(song_title, song_title)

        return song_title

    def normalize_music_title(self, title: str) -> str:
        """用于跨数据源匹配的轻量标题归一化。"""
        if not title:
            return ''
        title = unicodedata.normalize('NFKC', title)
        return re.sub(
            r'[\s\[\]\(\){}<>《》「」『』“”"\'\-_/／]',
            '',
            title.lower()
        )

    def match_music_from_catalog(self, song_title: str, catalog: List[Dict]) -> Optional[Dict]:
        normalized_title = self.normalize_music_title(song_title)
        if not normalized_title:
            return None

        for music in catalog:
            if normalized_title == self.normalize_music_title(music.get('title', '')):
                return music

        song_title_lower = song_title.lower()
        for music in catalog:
            music_title = music.get('title', '')
            music_title_lower = music_title.lower()
            normalized_music_title = self.normalize_music_title(music_title)

            if song_title_lower == music_title_lower:
                return music

            if (
                min(len(normalized_title), len(normalized_music_title)) >= 6
                and (normalized_title in normalized_music_title or normalized_music_title in normalized_title)
            ):
                return music

        return None

    def match_sekai_music(self, song_title: str) -> Optional[Dict]:
        """匹配 Sekai 音乐数据"""
        base_match = self.match_music_from_catalog(song_title, self.base_musics)
        if base_match:
            return base_match

        return self.match_music_from_catalog(song_title, self.sekai_musics)

    def normalize_unit_name(self, unit_name: str) -> str:
        unit_name_mapping = {
            'Wonderlands x Showtime': 'ワンダショ',
            '25-ji, Nightcord de.': '25時、ナイトコードで。',
        }
        return unit_name_mapping.get(unit_name, unit_name)

    def get_music_units(self, music_id: int) -> List[str]:
        """获取歌曲所属组合"""
        unit_mapping = {
            'light_music_club': 'Leo/need',
            'idol': 'MORE MORE JUMP!',
            'street': 'Vivid BAD SQUAD',
            'theme_park': 'ワンダショ',
            'school_refusal': '25時、ナイトコードで。',
            'vocaloid': 'Virtual Singer'
        }

        units = []
        for tag_entry in self.sekai_music_tags:
            if tag_entry['musicId'] == music_id:
                tag_type = tag_entry['musicTag']
                if tag_type in unit_mapping:
                    unit_name = unit_mapping[tag_type]
                    if unit_name not in units:
                        units.append(unit_name)

        return units

    def get_music_units_for_music(self, music: Dict) -> List[str]:
        """从最新曲库记录或 Sekai 标签表获取歌曲所属组合。"""
        unit_mapping = {
            'light_music_club': 'Leo/need',
            'idol': 'MORE MORE JUMP!',
            'street': 'Vivid BAD SQUAD',
            'theme_park': 'ワンダショ',
            'school_refusal': '25時、ナイトコードで。',
            'vocaloid': 'Virtual Singer'
        }

        units = []
        for tag in music.get('unitTags', []):
            unit_name = unit_mapping.get(tag)
            if unit_name and unit_name not in units:
                units.append(unit_name)

        for unit_name in music.get('units', []):
            normalized_name = self.normalize_unit_name(unit_name)
            if normalized_name and normalized_name not in units:
                units.append(normalized_name)

        if units:
            return units

        return self.get_music_units(music['id'])

    def extract_virtual_singers(self, video_title: str) -> List[str]:
        """从视频标题提取虚拟歌手"""
        singers = []
        singer_patterns = {
            '初音ミク': ['初音ミク', 'Miku'],
            '鏡音リン': ['鏡音リン', 'Rin'],
            '鏡音レン': ['鏡音レン', 'Len'],
            '巡音ルカ': ['巡音ルカ', 'Luka'],
            'MEIKO': ['MEIKO'],
            'KAITO': ['KAITO']
        }

        for singer, patterns in singer_patterns.items():
            for pattern in patterns:
                if pattern in video_title:
                    singers.append(singer)
                    break

        return singers

    def determine_video_type(self, video: Dict, song_title: str) -> str:
        """判断视频类型"""
        source_video_type = str(video.get('videoType') or '').strip()
        if source_video_type:
            return source_video_type

        title = video['title'].lower()
        desc = video['description'].lower()

        # 2DMV 检测
        if '2dmv' in title or 'アニメーション' in desc or '動画：' in video['description']:
            return 'official_2dmv'

        # 3DMV 检测
        if '3dmv' in title or 'game mv' in title:
            return 'official_3dmv'

        # 默认返回 official_2dmv（因为当前数据都是官方MV）
        return 'official_2dmv'

    def determine_variant(self, video: Dict) -> str:
        """判断视频变体"""
        version = self.determine_video_version(video)
        base = version['base']
        if base == 'sekai':
            return 'unit_version'
        if base == 'virtual_singer':
            return 'vs_version'
        if base == 'another_vocal':
            return 'another_vocal_version'
        if base == 'original':
            return 'original_version'
        return 'unknown_version'

    def normalize_version_base(self, value: Optional[str]) -> Optional[str]:
        if not value:
            return None

        normalized = str(value).strip().lower().replace(' ', '_').replace('-', '_')
        alias_map = {
            'base': 'original',
            'original': 'original',
            'original_version': 'original',
            'honke': 'original',
            'sekai': 'sekai',
            'sekai_ver': 'sekai',
            'unit': 'sekai',
            'unit_version': 'sekai',
            'virtual_singer': 'virtual_singer',
            'virtualsinger': 'virtual_singer',
            'vs': 'virtual_singer',
            'vs_version': 'virtual_singer',
            'another_vocal': 'another_vocal',
            'another': 'another_vocal',
            'another_vocal_version': 'another_vocal',
            'unknown': 'unknown',
        }
        return alias_map.get(normalized, normalized if normalized in self.VERSION_BASE_LABELS else None)

    def normalize_version_special_list(self, values: Any) -> List[str]:
        if not values:
            return []

        if isinstance(values, str):
            raw_values = [values]
        elif isinstance(values, list):
            raw_values = values
        else:
            return []

        alias_map = {
            'april_fool': 'april_fool',
            'aprilfool': 'april_fool',
            'april_fools': 'april_fool',
            '愚人节': 'april_fool',
            '愚人节版': 'april_fool',
            'エイプリルフール': 'april_fool',
        }

        normalized = []
        seen = set()
        for value in raw_values:
            key = alias_map.get(str(value).strip().lower().replace(' ', '_').replace('-', '_'))
            if not key or key in seen:
                continue
            seen.add(key)
            normalized.append(key)

        return normalized

    def build_version_label(self, base: str, special: List[str]) -> str:
        labels = []
        base_label = self.VERSION_BASE_LABELS.get(base)
        if base_label:
            labels.append(base_label)

        for special_key in self.VERSION_SPECIAL_ORDER:
            if special_key in special:
                labels.append(self.VERSION_SPECIAL_LABELS[special_key])

        return ' / '.join(labels) if labels else '未分类'

    def get_unit_version_label(self, units: List[str]) -> str:
        unit_names = [unit for unit in units if unit != 'Virtual Singer']
        if len(unit_names) == 1:
            return unit_names[0]
        return self.VERSION_BASE_LABELS['sekai']

    def apply_song_context_to_version(self, version: Dict[str, Any], units: List[str]) -> Dict[str, Any]:
        if version.get('base') != 'sekai':
            return version

        contextual_version = dict(version)
        contextual_version['label'] = self.get_unit_version_label(units)
        return contextual_version

    def get_mv_type_label(self, mv_type: Optional[str]) -> Optional[str]:
        if mv_type == 'mv_2d':
            return '游戏2D MV'
        if mv_type == 'mv':
            return '游戏3D MV'
        return None

    def extract_title_cast_segment(self, title: str) -> str:
        if ' / ' not in title:
            return ''
        return title.split(' / ', 1)[1].strip()

    def split_cast_tokens(self, cast_segment: str) -> List[str]:
        if not cast_segment:
            return []

        raw_tokens = re.split(r'\s*(?:×|&|,|／|/|\bwith\b)\s*', cast_segment, flags=re.IGNORECASE)
        tokens = [token.strip() for token in raw_tokens if token and token.strip()]
        return tokens

    def determine_cast_based_version(self, title: str) -> Optional[str]:
        cast_segment = self.extract_title_cast_segment(title)
        tokens = self.split_cast_tokens(cast_segment)
        if not tokens:
            return None

        token_flags = [
            any(singer_name in token for singer_name in self.VIRTUAL_SINGER_NAMES)
            for token in tokens
        ]

        if all(token_flags):
            return 'virtual_singer'

        if any(not flag for flag in token_flags) and len(tokens) > 1:
            return 'sekai'

        return None

    def apply_manual_version_override(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        raw_version = video.get('version')
        base = None
        special = []

        if isinstance(raw_version, dict):
            base = self.normalize_version_base(raw_version.get('base'))
            special = self.normalize_version_special_list(raw_version.get('special'))
        elif isinstance(raw_version, str):
            base = self.normalize_version_base(raw_version)

        if not base:
            base = self.normalize_version_base(video.get('versionBase'))
        if not special:
            special = self.normalize_version_special_list(video.get('versionSpecial'))

        if not base and not special:
            return None

        base = base or 'unknown'
        return {
            'base': base,
            'special': special,
            'label': self.build_version_label(base, special),
            'source': 'manual_override',
        }

    def determine_video_version(self, video: Dict[str, Any]) -> Dict[str, Any]:
        manual_override = self.apply_manual_version_override(video)
        if manual_override:
            return manual_override

        title = str(video.get('title') or '')
        lower_title = title.lower()

        special = []
        if any(marker in lower_title or marker in title for marker in self.APRIL_FOOL_MARKERS):
            special.append('april_fool')

        if any(marker in lower_title or marker in title for marker in self.ANOTHER_VOCAL_MARKERS):
            base = 'another_vocal'
        elif any(marker in lower_title or marker in title for marker in self.VIRTUAL_SINGER_MARKERS):
            base = 'virtual_singer'
        elif any(marker in lower_title or marker in title for marker in self.SEKAI_VERSION_MARKERS):
            base = 'sekai'
        elif any(marker in title for marker in self.UNIT_VERSION_MARKERS):
            base = 'sekai'
        elif any(marker in lower_title or marker in title for marker in self.ORIGINAL_VERSION_MARKERS):
            base = 'original'
        else:
            base = self.determine_cast_based_version(title) or 'unknown'

        return {
            'base': base,
            'special': special,
            'label': self.build_version_label(base, special),
            'source': 'title_heuristic',
        }

    def summarize_song_video_versions(
        self,
        video_entries: List[Dict[str, Any]],
        units: Optional[List[str]] = None,
        mv_type: Optional[str] = None
    ) -> Dict[str, Any]:
        base_values = []
        special_values = []
        label_values = []
        seen_bases = set()
        seen_special = set()
        seen_labels = set()

        for video in video_entries:
            version = video.get('version') or {}
            base = version.get('base', 'unknown')
            if base not in seen_bases:
                seen_bases.add(base)
                base_values.append(base)

            for special_key in version.get('special', []):
                if special_key not in seen_special:
                    seen_special.add(special_key)
                    special_values.append(special_key)

            label = version.get('label')
            if label and label not in seen_labels:
                seen_labels.add(label)
                label_values.append(label)

        base_values.sort(key=lambda value: self.VERSION_BASE_ORDER.index(value) if value in self.VERSION_BASE_ORDER else 999)
        special_values.sort(key=lambda value: self.VERSION_SPECIAL_ORDER.index(value) if value in self.VERSION_SPECIAL_ORDER else 999)

        display_labels = self.build_song_version_display_labels(base_values, special_values, units or [], mv_type)
        if not display_labels:
            display_labels = label_values

        return {
            'bases': base_values,
            'special': special_values,
            'labels': display_labels,
        }

    def build_song_version_display_labels(
        self,
        base_values: List[str],
        special_values: List[str],
        units: List[str],
        mv_type: Optional[str]
    ) -> List[str]:
        labels = []
        seen = set()

        def add_label(label: Optional[str]):
            if not label or label in seen:
                return
            seen.add(label)
            labels.append(label)

        for base in ['original', 'sekai', 'virtual_singer', 'another_vocal', 'unknown']:
            if base not in base_values:
                continue
            if base == 'sekai':
                add_label(self.get_unit_version_label(units))
            else:
                add_label(self.VERSION_BASE_LABELS.get(base, base))

        for special_key in self.VERSION_SPECIAL_ORDER:
            if special_key in special_values:
                add_label(self.VERSION_SPECIAL_LABELS.get(special_key, special_key))

        add_label(self.get_mv_type_label(mv_type))
        return labels

    def build_video_performer_extraction(self, video: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        extractors = self.normalize_extractors(video.get('extractors'))
        manual_performers = self.normalize_string_list(video.get('performers'))

        if 'performers' not in extractors and not manual_performers:
            return None

        return extract_video_performers(
            title=str(video.get('title') or ''),
            description=str(video.get('description') or ''),
            manual_performers=manual_performers,
        )

    def build_song_entry(self, song_title: str, videos: List[Dict]) -> Dict:
        """构建单个歌曲条目"""
        # 匹配 Sekai 数据
        sekai_music = self.match_sekai_music(song_title)

        if sekai_music:
            self.stats['matched_sekai'] += 1
            sekai_music_id = sekai_music['id']
            units = self.get_music_units_for_music(sekai_music)
            mv_type = 'mv_2d' if 'mv_2d' in sekai_music.get('categories', []) else 'mv'
        else:
            sekai_music_id = None
            units = []
            mv_type = None

        # 提取虚拟歌手
        virtual_singers = []
        for video in videos:
            singers = self.extract_virtual_singers(video['title'])
            for singer in singers:
                if singer not in virtual_singers:
                    virtual_singers.append(singer)

        # 获取别称
        aliases = []
        if song_title in self.aliases:
            aliases = self.aliases[song_title].get('aliases', [])

        # 生成标签
        tags = []
        if mv_type == 'mv_2d':
            tags.append('游戏2D MV')
        elif mv_type == 'mv':
            tags.append('游戏3D MV')
        tags.append('官方MV')
        tags.extend(units)
        tags.extend(virtual_singers)

        # 添加年份标签
        first_published_at = videos[0].get('publishedAt') if videos else None
        if first_published_at:
            year = first_published_at[:4]
            tags.append(f'{year}年')

        # 构建视频列表
        video_entries = []
        for video in videos:
            resolved_video = self.apply_original_video_override(video)
            version = self.apply_song_context_to_version(
                self.determine_video_version(resolved_video),
                units
            )
            performer_extraction = self.build_video_performer_extraction(resolved_video)
            video_entry = {
                'type': self.determine_video_type(resolved_video, song_title),
                'variant': self.determine_variant(resolved_video),
                'version': version,
                'videoId': resolved_video['videoId'],
                'url': resolved_video['url'],
                'title': resolved_video['title'],
                'description': resolved_video['description'],
                'channelTitle': resolved_video['channelTitle'],
                'channelId': resolved_video['channelId'],
                'uploadDate': resolved_video['publishedAt'],
                'thumbnails': resolved_video['thumbnails'],
                'playlistPosition': resolved_video['position'],
                'sourceKey': resolved_video.get('sourceKey'),
                'sourceName': resolved_video.get('sourceName'),
                'sourceKind': resolved_video.get('sourceKind'),
                'sourceUrl': resolved_video.get('sourceUrl'),
                'staff': build_video_staff(resolved_video.get('description', ''))
            }
            if performer_extraction:
                video_entry['performerExtraction'] = performer_extraction
            video_entries.append(video_entry)

        staff_summary = summarize_song_staff([video_entry['staff'] for video_entry in video_entries])
        performer_summary = summarize_song_performers(video_entries)
        video_version_summary = self.summarize_song_video_versions(video_entries, units, mv_type)

        # 构建歌曲条目
        song_entry = {
            'id': f'song_{song_title}',
            'sekaiMusicId': sekai_music_id,
            'title': song_title,
            'titleJp': song_title,
            'titleRomaji': None,
            'titleEn': None,
            'aliases': aliases,
            'creators': self._extract_creators(videos[0]) if videos else {},
            'classification': {
                'units': units,
                'virtualSingers': virtual_singers,
                'category': 'original',
                'mvType': mv_type,
                'tags': tags
            },
            'dates': {
                'sekaiReleaseDate': first_published_at[:10] if first_published_at else None,
                'youtubeUploadDate': first_published_at if first_published_at else None,
                'originalReleaseDate': None
            },
            'gameData': self._extract_game_data(sekai_music) if sekai_music else {},
            'videos': video_entries,
            'staffSummary': staff_summary,
            'performerSummary': performer_summary,
            'videoVersionSummary': video_version_summary,
        }

        return song_entry

    def _extract_creators(self, video: Dict) -> Dict:
        """从视频描述提取创作者信息"""
        desc = video['description']
        creators = {}

        # 提取作词作曲
        patterns = {
            'composer': r'作詞・作曲[：:]\\s*([^\\n\\s]+)',
            'lyricist': r'作詞[：:]\\s*([^\\n\\s]+)',
            'illustrator': r'イラスト[：:]\\s*([^\\n\\s]+)',
            'videoEditor': r'動画[：:]\\s*([^\\n\\s]+)',
            'lyricDesigner': r'リリックデザイン[：:]\\s*([^\\n\\s]+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, desc)
            if match:
                creators[key] = match.group(1).strip()

        return creators

    def _extract_game_data(self, sekai_music: Dict) -> Dict:
        """提取游戏数据"""
        if not sekai_music:
            return {}

        return {
            'difficulty': {
                'easy': None,
                'normal': None,
                'hard': None,
                'expert': None,
                'master': None
            },
            'duration': None,
            'bpm': None,
            'publishedAt': sekai_music.get('publishedAt')
        }

    def build_database(self) -> Dict:
        """构建完整数据库"""
        print("\n[BUILD] 开始构建数据库...")

        # 按歌曲名分组视频
        songs_dict = {}
        for video in self.youtube_data['videos']:
            song_title = video.get('songTitle') or self.extract_song_title(video['title'])

            if song_title not in songs_dict:
                songs_dict[song_title] = []
            songs_dict[song_title].append(video)

        print(f"[STATS] 识别到 {len(songs_dict)} 首不同的歌曲")

        # 构建歌曲条目
        songs = []
        for song_title, videos in songs_dict.items():
            song_entry = self.build_song_entry(song_title, videos)
            songs.append(song_entry)

            # 更新统计
            self.stats['total_videos'] += len(videos)
            for video in videos:
                resolved_video = self.apply_original_video_override(video)
                video_type = self.determine_video_type(resolved_video, song_title)
                self.stats['video_type_breakdown'][video_type] = \
                    self.stats['video_type_breakdown'].get(video_type, 0) + 1

            for unit in song_entry['classification']['units']:
                self.stats['unit_breakdown'][unit] = \
                    self.stats['unit_breakdown'].get(unit, 0) + 1

        self.stats['total_songs'] = len(songs)

        source_names = (
            [f'YouTube Snapshot ({name})' for name in (self.youtube_source_names or ([self.youtube_source_name] if self.youtube_source_name else []))]
            + [
                'Sekai Viewer musics.json',
                'Sekai Viewer musicTag.json',
                self.base_music_source,
                f'Manual aliases.json ({len(self.aliases)} songs)',
                f'Manual videos.json ({len(self.manual_videos)} videos)',
                f'Manual original_video_overrides.json ({len(self.original_video_overrides)} videos)'
            ]
        )

        # 构建最终数据库
        database = {
            'metadata': {
                'version': '2.2.0',
                'generatedAt': datetime.now().isoformat(),
                'sources': [source for source in source_names if source],
                'stats': {
                    'totalSongs': self.stats['total_songs'],
                    'totalVideos': self.stats['total_videos'],
                    'matchedSekai': self.stats['matched_sekai'],
                    'videoTypeBreakdown': self.stats['video_type_breakdown'],
                    'unitBreakdown': self.stats['unit_breakdown']
                }
            },
            'songs': songs
        }

        return database

    def save_database(self, database: Dict, output_path: str):
        """保存数据库"""
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(database, f, ensure_ascii=False, indent=2)

        print(f"\n[SUCCESS] 数据库已保存到: {output_file}")
        print(f"[INFO] 文件大小: {output_file.stat().st_size / 1024:.2f} KB")

    def export_staff_audits(self, database: Dict, output_dir: Path):
        """导出 staff 统计和人工复核文件"""
        output_dir.mkdir(parents=True, exist_ok=True)

        index_rows = build_staff_index_rows(database.get('songs', []))
        review_rows = build_staff_review_rows(database.get('songs', []))

        index_path = output_dir / 'video_staff_index.json'
        review_path = output_dir / 'staff_review.json'

        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_rows, f, ensure_ascii=False, indent=2)

        with open(review_path, 'w', encoding='utf-8') as f:
            json.dump(review_rows, f, ensure_ascii=False, indent=2)

        print(f"[OK] staff index generated: {index_path}")
        print(f"[OK] staff review generated: {review_path}")
        print(f"[INFO] staff index rows: {len(index_rows)}")
        print(f"[INFO] staff review rows: {len(review_rows)}")

    def export_original_credit_review(self, database: Dict, output_dir: Path):
        """导出原曲歌手抽取复核文件"""
        output_dir.mkdir(parents=True, exist_ok=True)

        review_rows = build_performer_review_rows(database.get('songs', []))
        review_path = output_dir / 'original_mv_review.json'

        with open(review_path, 'w', encoding='utf-8') as f:
            json.dump(review_rows, f, ensure_ascii=False, indent=2)

        print(f"[OK] original mv review generated: {review_path}")
        print(f"[INFO] original mv review rows: {len(review_rows)}")

    def print_stats(self):
        """打印统计信息"""
        print("\n" + "="*60)
        print("[STATS] 构建统计")
        print("="*60)
        print(f"总歌曲数: {self.stats['total_songs']}")
        print(f"总视频数: {self.stats['total_videos']}")
        print(f"匹配到 Sekai 数据: {self.stats['matched_sekai']}/{self.stats['total_songs']}")
        print(f"\n视频类型分布:")
        for vtype, count in self.stats['video_type_breakdown'].items():
            print(f"  {vtype}: {count}")
        print(f"\n组合分布:")
        for unit, count in sorted(self.stats['unit_breakdown'].items(), key=lambda x: -x[1]):
            print(f"  {unit}: {count}")
        print("="*60)


def main():
    # 设置基础路径
    base_path = Path(__file__).resolve().parents[1]

    # 创建构建器
    builder = DatabaseBuilder(str(base_path))

    # 加载数据
    builder.load_data()

    # 构建数据库
    database = builder.build_database()

    # 保存数据库
    output_path = os.path.join(str(base_path), "output", "database_v2.json")
    builder.save_database(database, output_path)
    builder.export_staff_audits(database, base_path / "output")
    builder.export_original_credit_review(database, base_path / "output")

    # 同步前端使用的别称文件
    sync_aliases(base_path)

    # 打印统计
    builder.print_stats()

    print("\n[COMPLETE] 构建完成！")


if __name__ == '__main__':
    main()
