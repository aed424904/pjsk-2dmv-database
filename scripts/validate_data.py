#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证脚本
检查生成的数据库是否符合规范
"""

import json
import re
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import parse_qs, urlparse


VIDEO_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{11}$")
ALLOWED_VIDEO_TYPES = {"official_2dmv", "original_mv"}
YOUTUBE_HOSTS = {"youtube.com", "www.youtube.com", "m.youtube.com", "youtu.be"}

class DataValidator:
    def __init__(self, database_path: str):
        with open(database_path, 'r', encoding='utf-8') as f:
            self.database = json.load(f)

        self.errors = []
        self.warnings = []

    def validate(self):
        """执行所有验证"""
        print("[INFO] 开始数据验证...\n")

        if not self.validate_structure():
            self.print_report()
            return False
        self.validate_metadata()
        self.validate_songs()
        self.validate_videos()
        self.validate_references()

        self.print_report()
        return not self.errors

    def validate_structure(self):
        """先验证顶层结构，避免后续遍历因类型错误中断。"""
        print("[CHECK] 验证顶层结构...")
        if not isinstance(self.database, dict):
            self.errors.append("数据库顶层必须是对象")
            return False
        if not isinstance(self.database.get('metadata'), dict):
            self.errors.append("metadata 必须是对象")
        if not isinstance(self.database.get('songs'), list):
            self.errors.append("songs 必须是数组")
        return not self.errors

    def validate_metadata(self):
        """验证元数据"""
        print("[CHECK] 验证元数据...")
        metadata = self.database.get('metadata', {})

        required_fields = ['version', 'generatedAt', 'sources', 'stats']
        for field in required_fields:
            if field not in metadata:
                self.errors.append(f"metadata 缺少必填字段: {field}")

        if not isinstance(metadata.get('version'), str) or not metadata.get('version', '').strip():
            self.errors.append("metadata.version 必须是非空字符串")
        if not isinstance(metadata.get('generatedAt'), str) or not metadata.get('generatedAt', '').strip():
            self.errors.append("metadata.generatedAt 必须是非空字符串")
        if not isinstance(metadata.get('sources'), list) or not metadata.get('sources'):
            self.errors.append("metadata.sources 必须是非空数组")
        if not isinstance(metadata.get('stats'), dict):
            self.errors.append("metadata.stats 必须是对象")
            return

        if metadata.get('stats', {}).get('totalSongs', 0) != len(self.database.get('songs', [])):
            self.errors.append("metadata.stats.totalSongs 与实际歌曲数不符")

        actual_video_count = sum(len(song.get('videos', [])) for song in self.database.get('songs', []))
        if metadata.get('stats', {}).get('totalVideos', 0) != actual_video_count:
            self.errors.append("metadata.stats.totalVideos 与实际视频数不符")

    def validate_songs(self):
        """验证歌曲数据"""
        print("[CHECK] 验证歌曲数据...")

        song_ids = set()
        sekai_music_ids = set()
        for idx, song in enumerate(self.database.get('songs', [])):
            if not isinstance(song, dict):
                self.errors.append(f"歌曲 #{idx} 必须是对象")
                continue
            # 检查必填字段
            required = ['id', 'title', 'videos']
            for field in required:
                if field not in song:
                    self.errors.append(f"歌曲 #{idx} 缺少必填字段: {field}")

            # 检查 ID 唯一性
            song_id = song.get('id')
            if song_id is None or not str(song_id).strip():
                self.errors.append(f"歌曲 #{idx} 的 id 不能为空")
            if song_id in song_ids:
                self.errors.append(f"重复的歌曲 ID: {song_id}")
            song_ids.add(song_id)

            sekai_music_id = song.get('sekaiMusicId')
            if sekai_music_id is not None:
                if sekai_music_id in sekai_music_ids:
                    self.errors.append(f"重复的 Sekai Music ID: {sekai_music_id}")
                sekai_music_ids.add(sekai_music_id)

            if not isinstance(song.get('title'), str) or not song.get('title', '').strip():
                self.errors.append(f"歌曲 {song_id} 的 title 必须是非空字符串")
            if not isinstance(song.get('videos'), list):
                self.errors.append(f"歌曲 {song_id} 的 videos 必须是数组")
                continue

            # 检查视频列表
            if not song.get('videos'):
                self.warnings.append(f"歌曲 {song.get('title')} 没有关联的视频")

    def validate_videos(self):
        """验证视频数据"""
        print("[CHECK] 验证视频数据...")

        video_ids = set()
        for song in self.database.get('songs', []):
            if not isinstance(song, dict) or not isinstance(song.get('videos'), list):
                continue
            for video in song.get('videos', []):
                if not isinstance(video, dict):
                    self.errors.append(f"视频必须是对象 (歌曲: {song.get('title')})")
                    continue
                # 检查必填字段
                required = ['type', 'videoId', 'url', 'title']
                for field in required:
                    if field not in video:
                        self.errors.append(
                            f"视频缺少必填字段: {field} (歌曲: {song.get('title')})"
                        )

                # 检查视频 ID 唯一性
                video_id = video.get('videoId')
                if not isinstance(video_id, str) or not VIDEO_ID_PATTERN.fullmatch(video_id):
                    self.errors.append(f"无效的 YouTube videoId: {video_id} (歌曲: {song.get('title')})")
                if video_id in video_ids:
                    self.errors.append(f"重复的视频 ID: {video_id}")
                video_ids.add(video_id)

                video_type = video.get('type')
                if video_type not in ALLOWED_VIDEO_TYPES:
                    self.errors.append(f"未知的视频类型: {video_type} (视频: {video_id})")
                if not isinstance(video.get('title'), str) or not video.get('title', '').strip():
                    self.errors.append(f"视频 title 必须是非空字符串 (视频: {video_id})")
                if not self.is_matching_youtube_url(video.get('url'), video_id):
                    self.errors.append(f"无效或不匹配的 YouTube URL (视频: {video_id})")

    @staticmethod
    def is_matching_youtube_url(url, video_id):
        if not isinstance(url, str) or not isinstance(video_id, str):
            return False
        try:
            parsed = urlparse(url)
        except ValueError:
            return False
        host = (parsed.hostname or '').lower()
        if parsed.scheme not in {'http', 'https'} or host not in YOUTUBE_HOSTS:
            return False
        if host == 'youtu.be':
            url_video_id = parsed.path.strip('/').split('/')[0]
        elif parsed.path == '/watch':
            url_video_id = parse_qs(parsed.query).get('v', [''])[0]
        elif parsed.path.startswith('/shorts/') or parsed.path.startswith('/embed/'):
            url_video_id = parsed.path.strip('/').split('/')[1]
        else:
            return False
        return url_video_id == video_id

    def validate_references(self):
        """验证引用完整性"""
        print("[CHECK] 验证引用完整性...")

        songs = self.database.get('songs', [])
        stats = self.database.get('metadata', {}).get('stats', {})

        matched_sekai = sum(1 for song in songs if isinstance(song, dict) and song.get('sekaiMusicId'))
        if stats.get('matchedSekai') != matched_sekai:
            self.errors.append("metadata.stats.matchedSekai 与实际匹配歌曲数不符")

        video_type_breakdown = Counter()
        unit_breakdown = Counter()
        for song in songs:
            if not isinstance(song, dict):
                continue
            for video in song.get('videos', []) if isinstance(song.get('videos'), list) else []:
                if isinstance(video, dict) and video.get('type'):
                    video_type_breakdown[video['type']] += 1
            classification = song.get('classification', {})
            units = classification.get('units', []) if isinstance(classification, dict) else []
            if isinstance(units, list):
                unit_breakdown.update(unit for unit in units if isinstance(unit, str) and unit)

        if stats.get('videoTypeBreakdown') != dict(video_type_breakdown):
            self.errors.append("metadata.stats.videoTypeBreakdown 与实际视频类型分布不符")
        if stats.get('unitBreakdown') != dict(unit_breakdown):
            self.errors.append("metadata.stats.unitBreakdown 与实际组合分布不符")

    def print_report(self):
        """打印验证报告"""
        print("\n" + "="*60)
        print("[REPORT] 验证报告")
        print("="*60)

        if not self.errors and not self.warnings:
            print("[OK] 验证通过！数据库结构完整。")
        else:
            if self.errors:
                print(f"\n[ERROR] 发现 {len(self.errors)} 个错误:")
                for error in self.errors:
                    print(f"  - {error}")

            if self.warnings:
                print(f"\n[WARNING] 发现 {len(self.warnings)} 个警告:")
                for warning in self.warnings:
                    print(f"  - {warning}")

        print("="*60)


def main():
    base_path = Path(__file__).resolve().parents[1]
    database_path = Path(sys.argv[1]) if len(sys.argv) > 1 else base_path / "output" / "database_v2.json"

    try:
        validator = DataValidator(str(database_path))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"[ERROR] 无法读取数据库: {exc}")
        return 1
    return 0 if validator.validate() else 1


if __name__ == '__main__':
    raise SystemExit(main())
