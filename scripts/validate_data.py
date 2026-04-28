#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据验证脚本
检查生成的数据库是否符合规范
"""

import json
from pathlib import Path
from typing import Dict, List

class DataValidator:
    def __init__(self, database_path: str):
        with open(database_path, 'r', encoding='utf-8') as f:
            self.database = json.load(f)

        self.errors = []
        self.warnings = []

    def validate(self):
        """执行所有验证"""
        print("[INFO] 开始数据验证...\n")

        self.validate_metadata()
        self.validate_songs()
        self.validate_videos()
        self.validate_references()

        self.print_report()

    def validate_metadata(self):
        """验证元数据"""
        print("[CHECK] 验证元数据...")
        metadata = self.database.get('metadata', {})

        required_fields = ['version', 'generatedAt', 'sources', 'stats']
        for field in required_fields:
            if field not in metadata:
                self.errors.append(f"metadata 缺少必填字段: {field}")

        if metadata.get('stats', {}).get('totalSongs', 0) != len(self.database.get('songs', [])):
            self.errors.append("metadata.stats.totalSongs 与实际歌曲数不符")

    def validate_songs(self):
        """验证歌曲数据"""
        print("[CHECK] 验证歌曲数据...")

        song_ids = set()
        for idx, song in enumerate(self.database.get('songs', [])):
            # 检查必填字段
            required = ['id', 'title', 'videos']
            for field in required:
                if field not in song:
                    self.errors.append(f"歌曲 #{idx} 缺少必填字段: {field}")

            # 检查 ID 唯一性
            song_id = song.get('id')
            if song_id in song_ids:
                self.errors.append(f"重复的歌曲 ID: {song_id}")
            song_ids.add(song_id)

            # 检查视频列表
            if not song.get('videos'):
                self.warnings.append(f"歌曲 {song.get('title')} 没有关联的视频")

    def validate_videos(self):
        """验证视频数据"""
        print("[CHECK] 验证视频数据...")

        video_ids = set()
        for song in self.database.get('songs', []):
            for video in song.get('videos', []):
                # 检查必填字段
                required = ['type', 'videoId', 'url', 'title']
                for field in required:
                    if field not in video:
                        self.errors.append(
                            f"视频缺少必填字段: {field} (歌曲: {song.get('title')})"
                        )

                # 检查视频 ID 唯一性
                video_id = video.get('videoId')
                if video_id in video_ids:
                    self.warnings.append(f"重复的视频 ID: {video_id}")
                video_ids.add(video_id)

    def validate_references(self):
        """验证引用完整性"""
        print("[CHECK] 验证引用完整性...")

        # 这里可以添加更多验证，例如：
        # - sekaiMusicId 是否存在于 Sekai 数据中
        # - units 名称是否合法
        # - virtualSingers 名称是否合法
        pass

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
    database_path = r"C:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\output\database_v2.json"

    validator = DataValidator(database_path)
    validator.validate()


if __name__ == '__main__':
    main()
