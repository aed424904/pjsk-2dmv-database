#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
缓存管理模块
负责缓存已抓取的视频信息，避免重复请求
"""

import os
import json
import time
from typing import Optional, Dict
from datetime import datetime, timedelta


class CacheManager:
    """缓存管理器"""

    def __init__(self, cache_dir: str = 'output/cache', expiry_days: int = 7):
        """
        初始化缓存管理器

        Args:
            cache_dir: 缓存目录路径
            expiry_days: 缓存有效期（天）
        """
        self.cache_dir = cache_dir
        self.expiry_days = expiry_days

        # 确保缓存目录存在
        os.makedirs(os.path.join(cache_dir, 'youtube'), exist_ok=True)
        os.makedirs(os.path.join(cache_dir, 'niconico'), exist_ok=True)

    def get(self, platform: str, video_id: str) -> Optional[Dict]:
        """
        从缓存读取视频信息

        Args:
            platform: 平台名称 (youtube/niconico)
            video_id: 视频 ID

        Returns:
            缓存的视频信息，如果不存在或已过期则返回 None
        """
        cache_file = self._get_cache_path(platform, video_id)

        if not os.path.exists(cache_file):
            return None

        # 检查是否过期
        if self.is_expired(cache_file):
            return None

        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return None

    def set(self, platform: str, video_id: str, data: Dict) -> bool:
        """
        写入缓存

        Args:
            platform: 平台名称 (youtube/niconico)
            video_id: 视频 ID
            data: 视频信息数据

        Returns:
            是否写入成功
        """
        cache_file = self._get_cache_path(platform, video_id)

        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"❌ 缓存写入失败 ({video_id}): {e}")
            return False

    def is_expired(self, cache_file: str) -> bool:
        """
        检查缓存是否过期

        Args:
            cache_file: 缓存文件路径

        Returns:
            是否已过期
        """
        try:
            file_time = os.path.getmtime(cache_file)
            file_datetime = datetime.fromtimestamp(file_time)
            expiry_datetime = datetime.now() - timedelta(days=self.expiry_days)
            return file_datetime < expiry_datetime
        except Exception:
            return True

    def clear_expired(self) -> int:
        """
        清理过期缓存

        Returns:
            清理的文件数量
        """
        cleared_count = 0

        for platform in ['youtube', 'niconico']:
            platform_dir = os.path.join(self.cache_dir, platform)
            if not os.path.exists(platform_dir):
                continue

            for filename in os.listdir(platform_dir):
                if not filename.endswith('.json'):
                    continue

                cache_file = os.path.join(platform_dir, filename)
                if self.is_expired(cache_file):
                    try:
                        os.remove(cache_file)
                        cleared_count += 1
                    except Exception:
                        pass

        return cleared_count

    def _get_cache_path(self, platform: str, video_id: str) -> str:
        """获取缓存文件路径"""
        return os.path.join(self.cache_dir, platform, f'{video_id}.json')

    def get_cache_stats(self) -> Dict:
        """
        获取缓存统计信息

        Returns:
            缓存统计数据
        """
        stats = {
            'youtube': 0,
            'niconico': 0,
            'total': 0,
        }

        for platform in ['youtube', 'niconico']:
            platform_dir = os.path.join(self.cache_dir, platform)
            if os.path.exists(platform_dir):
                count = len([f for f in os.listdir(platform_dir) if f.endswith('.json')])
                stats[platform] = count
                stats['total'] += count

        return stats


# 测试代码
if __name__ == '__main__':
    cache_mgr = CacheManager(cache_dir='../output/cache')

    # 测试写入
    test_data = {
        'title': 'Test Video',
        'duration': 240,
        'viewCount': 100000,
    }

    cache_mgr.set('youtube', 'TEST_VIDEO_ID', test_data)

    # 测试读取
    cached = cache_mgr.get('youtube', 'TEST_VIDEO_ID')
    if cached:
        print(f"✅ 缓存读取成功: {cached['title']}")
    else:
        print("❌ 缓存读取失败")

    # 获取统计
    stats = cache_mgr.get_cache_stats()
    print(f"📊 缓存统计: {stats}")
