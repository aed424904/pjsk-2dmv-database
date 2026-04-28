#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
URL 解析模块
负责解析视频链接，识别平台和提取视频 ID
"""

import re
from typing import Dict, Optional
from urllib.parse import urlparse, parse_qs


class URLParser:
    """URL 解析器"""

    @staticmethod
    def parse_url(url: str) -> Optional[Dict[str, str]]:
        """
        解析视频 URL，识别平台和提取 ID

        Args:
            url: 视频链接

        Returns:
            {
                'platform': 'youtube' | 'niconico',
                'video_id': '视频 ID',
                'normalized_url': '标准化 URL'
            }
            如果无法解析则返回 None
        """
        if URLParser.is_youtube(url):
            video_id = URLParser.extract_youtube_id(url)
            if video_id:
                return {
                    'platform': 'youtube',
                    'video_id': video_id,
                    'normalized_url': f'https://www.youtube.com/watch?v={video_id}'
                }

        elif URLParser.is_niconico(url):
            video_id = URLParser.extract_niconico_id(url)
            if video_id:
                return {
                    'platform': 'niconico',
                    'video_id': video_id,
                    'normalized_url': f'https://www.nicovideo.jp/watch/{video_id}'
                }

        return None

    @staticmethod
    def is_youtube(url: str) -> bool:
        """判断是否为 YouTube 链接"""
        return 'youtube.com' in url or 'youtu.be' in url

    @staticmethod
    def is_niconico(url: str) -> bool:
        """判断是否为 Niconico 链接"""
        return 'nicovideo.jp' in url or 'nico.ms' in url

    @staticmethod
    def extract_youtube_id(url: str) -> Optional[str]:
        """
        提取 YouTube 视频 ID

        支持格式：
        - https://www.youtube.com/watch?v=VIDEO_ID
        - https://youtu.be/VIDEO_ID
        - https://youtube.com/watch?v=VIDEO_ID
        """
        # youtu.be 短链接格式
        if 'youtu.be' in url:
            match = re.search(r'youtu\.be/([a-zA-Z0-9_-]+)', url)
            if match:
                return match.group(1)

        # youtube.com 标准格式
        parsed = urlparse(url)
        if parsed.hostname in ('www.youtube.com', 'youtube.com', 'm.youtube.com'):
            if parsed.path == '/watch':
                query = parse_qs(parsed.query)
                if 'v' in query:
                    return query['v'][0]

        # 备用正则匹配
        match = re.search(r'[?&]v=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)

        return None

    @staticmethod
    def extract_niconico_id(url: str) -> Optional[str]:
        """
        提取 Niconico 视频 ID

        支持格式：
        - https://www.nicovideo.jp/watch/sm12345678
        - https://nico.ms/sm12345678
        """
        # 匹配 sm/nm 开头的视频 ID
        match = re.search(r'/(sm\d+|nm\d+|so\d+)', url)
        if match:
            return match.group(1)

        return None


# 测试代码
if __name__ == '__main__':
    # 测试 YouTube URL
    test_urls = [
        'https://youtu.be/PqJNc9KVIZE',
        'https://www.youtube.com/watch?v=Xg-qfsKN2_E',
        'https://www.nicovideo.jp/watch/sm9874560',
    ]

    for url in test_urls:
        result = URLParser.parse_url(url)
        if result:
            print(f"✅ {url}")
            print(f"   Platform: {result['platform']}")
            print(f"   Video ID: {result['video_id']}")
            print(f"   Normalized: {result['normalized_url']}\n")
        else:
            print(f"❌ 无法解析: {url}\n")
