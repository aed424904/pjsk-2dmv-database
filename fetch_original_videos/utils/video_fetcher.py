#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
视频信息抓取模块
使用 yt-dlp 抓取 YouTube 和 Niconico 视频的元数据
"""

import yt_dlp
import time
from typing import Dict, List, Optional
from datetime import datetime

from .url_parser import URLParser
from .cache_manager import CacheManager
from .error_handler import ErrorHandler, RetryConfig


class VideoFetcher:
    """视频信息抓取器"""

    def __init__(
        self,
        ytdlp_opts: Optional[Dict] = None,
        use_cache: bool = True,
        cache_dir: str = 'output/cache',
        cache_expiry_days: int = 7,
        retry_config: Optional[RetryConfig] = None,
        proxy: Optional[str] = None
    ):
        """
        初始化视频抓取器

        Args:
            ytdlp_opts: yt-dlp 配置选项
            use_cache: 是否使用缓存
            cache_dir: 缓存目录
            cache_expiry_days: 缓存有效期（天）
            retry_config: 重试配置
            proxy: 代理服务器地址
        """
        # 默认 yt-dlp 配置
        default_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
            'socket_timeout': 30,
            'ignoreerrors': True,
            'no_check_certificate': True,
        }

        # 合并用户配置
        self.ytdlp_opts = {**default_opts, **(ytdlp_opts or {})}

        # 添加代理配置
        if proxy:
            self.ytdlp_opts['proxy'] = proxy

        # 初始化缓存管理器
        self.use_cache = use_cache
        self.cache_manager = CacheManager(cache_dir, cache_expiry_days) if use_cache else None

        # 初始化错误处理器
        self.error_handler = ErrorHandler(retry_config)

        # 统计信息
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cached': 0,
        }

    def fetch_video_info(self, url: str, video_data: Dict) -> Dict:
        """
        抓取单个视频信息

        Args:
            url: 视频链接
            video_data: 视频基本信息 (id, musicId, videoLink)

        Returns:
            标准化的视频信息数据
        """
        # 解析 URL
        parsed = URLParser.parse_url(url)
        if not parsed:
            return self._create_error_result(
                video_data,
                'URL解析失败',
                'PARSE_ERROR',
                1
            )

        platform = parsed['platform']
        video_id = parsed['video_id']
        normalized_url = parsed['normalized_url']

        # 检查缓存
        if self.use_cache:
            cached_data = self.cache_manager.get(platform, video_id)
            if cached_data:
                self.stats['cached'] += 1
                # 合并基本信息
                return {
                    **video_data,
                    **cached_data,
                    'platform': platform,
                    'videoId': video_id,
                }

        # 使用错误处理器带重试地抓取
        result = self.error_handler.retry_on_error(
            self._fetch_with_ytdlp,
            normalized_url
        )

        if result['success']:
            # 抓取成功
            metadata = result['data']
            video_info = {
                **video_data,
                'platform': platform,
                'videoId': video_id,
                'metadata': metadata,
                'fetchedAt': datetime.now().isoformat(),
                'status': 'success',
            }

            # 写入缓存
            if self.use_cache:
                cache_data = {
                    'metadata': metadata,
                    'fetchedAt': video_info['fetchedAt'],
                    'status': 'success',
                }
                self.cache_manager.set(platform, video_id, cache_data)

            self.stats['success'] += 1
            return video_info

        else:
            # 抓取失败
            self.stats['failed'] += 1
            return self._create_error_result(
                {**video_data, 'platform': platform, 'videoId': video_id},
                result['error'],
                result['error_type'],
                result['attempts']
            )

    def _fetch_with_ytdlp(self, url: str) -> Dict:
        """
        使用 yt-dlp 抓取视频信息

        Args:
            url: 视频链接

        Returns:
            提取的元数据

        Raises:
            Exception: 抓取失败时抛出异常
        """
        with yt_dlp.YoutubeDL(self.ytdlp_opts) as ydl:
            info = ydl.extract_info(url, download=False)

            if not info:
                raise Exception("Failed to extract video information")

            # 提取需要的字段
            return self._extract_metadata(info)

    def _extract_metadata(self, ydl_info: Dict) -> Dict:
        """
        从 yt-dlp 原始数据提取需要的字段

        Args:
            ydl_info: yt-dlp 返回的原始数据

        Returns:
            标准化的元数据
        """
        return {
            'title': ydl_info.get('title', ''),
            'description': ydl_info.get('description', ''),
            'uploader': ydl_info.get('uploader', ''),
            'uploaderId': ydl_info.get('uploader_id', '') or ydl_info.get('channel_id', ''),
            'uploadDate': ydl_info.get('upload_date', ''),
            'duration': ydl_info.get('duration', 0),
            'viewCount': ydl_info.get('view_count', 0),
            'likeCount': ydl_info.get('like_count', 0),
            'commentCount': ydl_info.get('comment_count'),
            'thumbnailUrl': ydl_info.get('thumbnail', ''),
            'tags': ydl_info.get('tags', []) or [],
        }

    def _create_error_result(
        self,
        video_data: Dict,
        error: str,
        error_type: str,
        attempts: int
    ) -> Dict:
        """创建错误结果"""
        return {
            **video_data,
            'metadata': None,
            'fetchedAt': datetime.now().isoformat(),
            'status': 'failed',
            'error': error,
            'errorType': error_type,
            'attempts': attempts,
        }

    def fetch_batch(
        self,
        video_list: List[Dict],
        delay: float = 1.5,
        progress_callback=None
    ) -> List[Dict]:
        """
        批量抓取视频信息

        Args:
            video_list: 视频列表 [{id, musicId, videoLink}, ...]
            delay: 每个请求之间的延迟（秒）
            progress_callback: 进度回调函数 callback(current, total)

        Returns:
            抓取结果列表
        """
        results = []
        total = len(video_list)

        for index, video in enumerate(video_list, 1):
            self.stats['total'] += 1

            # 抓取视频信息
            result = self.fetch_video_info(video['videoLink'], video)
            results.append(result)

            # 调用进度回调
            if progress_callback:
                progress_callback(index, total, result)

            # 延迟（最后一个不需要延迟）
            if index < total:
                time.sleep(delay)

        return results

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return self.stats.copy()

    def reset_stats(self):
        """重置统计信息"""
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'cached': 0,
        }


# 测试代码
if __name__ == '__main__':
    # 测试单个视频抓取
    fetcher = VideoFetcher(use_cache=True, cache_dir='../output/cache')

    test_video = {
        'id': 1,
        'musicId': 1,
        'videoLink': 'https://youtu.be/PqJNc9KVIZE'
    }

    print("🚀 开始测试视频抓取...")
    result = fetcher.fetch_video_info(test_video['videoLink'], test_video)

    if result['status'] == 'success':
        print(f"✅ 抓取成功!")
        print(f"   标题: {result['metadata']['title']}")
        print(f"   时长: {result['metadata']['duration']} 秒")
        print(f"   观看: {result['metadata']['viewCount']:,}")
    else:
        print(f"❌ 抓取失败: {result.get('error', 'Unknown error')}")

    print(f"\n📊 统计: {fetcher.get_stats()}")
