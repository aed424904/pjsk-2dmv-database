#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
YouTube Playlist 视频信息抓取工具
支持混合方案：优先使用 YouTube Data API v3，备用 yt-dlp
"""

import json
import os
import re
import time
from datetime import datetime
from urllib.parse import urlparse, parse_qs

try:
    import requests
except ImportError:
    requests = None

DEFAULT_API_KEY = os.getenv('YOUTUBE_API_KEY')


class YouTubePlaylistFetcher:
    """YouTube Playlist 抓取器"""

    def __init__(self, api_key=None, request_timeout=(5, 30), max_retries=3, retry_backoff=1.0):
        """
        初始化抓取器

        Args:
            api_key: YouTube Data API v3 密钥（可选）
        """
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.results = []
        self.request_timeout = request_timeout
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff = max(0.0, float(retry_backoff))

    def request_api(self, endpoint, params):
        """发送带超时和有限重试的 YouTube Data API GET 请求。"""
        if requests is None:
            raise RuntimeError("未安装 requests")

        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        retryable_statuses = {429, 500, 502, 503, 504}

        for attempt in range(self.max_retries + 1):
            try:
                response = requests.get(url, params=params, timeout=self.request_timeout)
            except requests.RequestException:
                if attempt >= self.max_retries:
                    raise
                delay = self.retry_backoff * (2 ** attempt)
                print(f"[WARN] API 网络错误，{delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})")
                time.sleep(delay)
                continue

            if response.status_code not in retryable_statuses or attempt >= self.max_retries:
                return response

            retry_after = response.headers.get('Retry-After', '')
            try:
                delay = max(0.0, float(retry_after))
            except (TypeError, ValueError):
                delay = self.retry_backoff * (2 ** attempt)
            print(f"[WARN] API 返回 {response.status_code}，{delay:.1f} 秒后重试 ({attempt + 1}/{self.max_retries})")
            time.sleep(delay)

        raise RuntimeError("YouTube API 重试流程异常结束")

    def extract_playlist_id(self, url):
        """从 URL 提取 Playlist ID"""
        parsed = urlparse(url)
        if 'list' in parse_qs(parsed.query):
            return parse_qs(parsed.query)['list'][0]
        return None

    def extract_video_id(self, url):
        """从 URL 提取 Video ID"""
        # 支持多种 YouTube URL 格式
        patterns = [
            r'(?:youtube\.com\/watch\?v=|youtu\.be\/)([a-zA-Z0-9_-]{11})',
            r'youtube\.com\/embed\/([a-zA-Z0-9_-]{11})',
        ]
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None

    def build_video_info_from_api_snippet(self, snippet, video_id=None, statistics=None):
        """从 YouTube API snippet 构建标准视频信息。

        playlistItems.snippet 的 channelTitle 是播放列表所属频道；真实投稿者在
        videoOwnerChannelTitle/videoOwnerChannelId，或 videos.list 的 snippet.channelTitle/channelId。
        statistics 来自 videos.list 的 statistics 部分，包含 viewCount、likeCount 等。
        """
        resource_id = snippet.get('resourceId') or {}
        resolved_video_id = video_id or resource_id.get('videoId', '')

        channel_title = (
            snippet.get('videoOwnerChannelTitle')
            or snippet.get('channelTitle')
            or ''
        )
        channel_id = (
            snippet.get('videoOwnerChannelId')
            or snippet.get('channelId')
            or ''
        )

        info = {
            'videoId': resolved_video_id,
            'url': f'https://www.youtube.com/watch?v={resolved_video_id}',
            'title': snippet.get('title', ''),
            'description': snippet.get('description', ''),
            'channelTitle': channel_title,
            'channelId': channel_id,
            'publishedAt': snippet.get('publishedAt', ''),
            'thumbnails': {
                'default': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                'medium': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                'high': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                'standard': snippet.get('thumbnails', {}).get('standard', {}).get('url', ''),
                'maxres': snippet.get('thumbnails', {}).get('maxres', {}).get('url', '')
            },
            'position': snippet.get('position', 0)
        }

        if statistics:
            info['viewCount'] = int(statistics.get('viewCount', 0)) if statistics.get('viewCount') else 0
            info['likeCount'] = int(statistics.get('likeCount', 0)) if statistics.get('likeCount') else 0

        return info

    def fetch_video_details_map(self, video_ids):
        """批量获取 videos.list 详情，用真实视频 snippet 覆盖 playlistItem 元数据。"""
        if not video_ids or not self.api_key or requests is None:
            return {}

        details = {}
        for start in range(0, len(video_ids), 50):
            batch = [video_id for video_id in video_ids[start:start + 50] if video_id]
            if not batch:
                continue

            response = self.request_api(
                "videos",
                {
                    'part': 'snippet,statistics',
                    'id': ','.join(batch),
                    'key': self.api_key,
                    'maxResults': 50,
                },
            )

            if response.status_code != 200:
                print(f"⚠️  视频详情请求失败: {response.status_code}")
                print(f"   错误信息: {response.text}")
                continue

            payload = response.json()
            for item in payload.get('items', []):
                video_id = item.get('id')
                snippet = item.get('snippet') or {}
                statistics = item.get('statistics') or {}
                if video_id and snippet:
                    details[video_id] = self.build_video_info_from_api_snippet(snippet, video_id=video_id, statistics=statistics)

            time.sleep(0.2)

        return details

    def merge_video_details(self, videos, details_map):
        """保留 playlist 位置/source 字段，同时用真实视频详情覆盖标题、频道、发布时间等。"""
        if not details_map:
            return videos

        enriched = []
        for video in videos:
            video_id = video.get('videoId')
            detail = details_map.get(video_id)
            if not detail:
                enriched.append(video)
                continue

            merged = {
                **video,
                'title': detail.get('title') or video.get('title', ''),
                'description': detail.get('description') or video.get('description', ''),
                'channelTitle': detail.get('channelTitle') or video.get('channelTitle', ''),
                'channelId': detail.get('channelId') or video.get('channelId', ''),
                'publishedAt': detail.get('publishedAt') or video.get('publishedAt', ''),
                'thumbnails': detail.get('thumbnails') or video.get('thumbnails', {}),
                'viewCount': detail.get('viewCount') if detail.get('viewCount') is not None else video.get('viewCount', 0),
                'likeCount': detail.get('likeCount') if detail.get('likeCount') is not None else video.get('likeCount', 0),
            }
            enriched.append(merged)

        return enriched

    def fetch_with_api(self, playlist_id, max_results=500):
        """
        使用 YouTube Data API v3 获取 Playlist 信息

        Args:
            playlist_id: Playlist ID
            max_results: 最大结果数（默认500，API 单次最多50）

        Returns:
            list: 视频信息列表
        """
        if not self.api_key:
            print("❌ 未提供 API Key，无法使用 API 方式")
            return None
        if requests is None:
            print("⚠️  未安装 requests，跳过 API 方式并回退到 yt-dlp")
            return None

        print(f"📡 使用 YouTube Data API v3 抓取...")
        videos = []
        next_page_token = None
        page_count = 0

        try:
            while True:
                page_count += 1
                print(f"  - 正在获取第 {page_count} 页...")

                # 构建请求 URL
                url = f"{self.base_url}/playlistItems"
                params = {
                    'part': 'snippet,contentDetails',
                    'playlistId': playlist_id,
                    'maxResults': min(50, max_results - len(videos)),  # API 单次最多 50
                    'key': self.api_key
                }

                if next_page_token:
                    params['pageToken'] = next_page_token

                # 发送请求
                response = self.request_api("playlistItems", params)

                if response.status_code != 200:
                    print(f"❌ API 请求失败: {response.status_code}")
                    print(f"   错误信息: {response.text}")
                    return None

                data = response.json()

                # 解析视频信息
                for item in data.get('items', []):
                    snippet = item['snippet']
                    video_id = snippet['resourceId']['videoId']

                    video_info = self.build_video_info_from_api_snippet(snippet, video_id=video_id)
                    videos.append(video_info)

                print(f"    ✓ 已获取 {len(videos)} 个视频")

                # 检查是否还有下一页
                next_page_token = data.get('nextPageToken')
                if not next_page_token or len(videos) >= max_results:
                    break

                # 避免请求过快
                time.sleep(0.5)

            print("  - 正在补全真实视频投稿账号...")
            details_map = self.fetch_video_details_map([video['videoId'] for video in videos])
            videos = self.merge_video_details(videos, details_map)
            print(f"✅ API 抓取完成，共获取 {len(videos)} 个视频，补全详情 {len(details_map)} 条")
            return videos

        except Exception as e:
            print(f"❌ API 抓取出错: {str(e)}")
            return None

    def fetch_with_ytdlp(self, playlist_url):
        """
        使用 yt-dlp 获取 Playlist 信息（备用方案）

        Args:
            playlist_url: Playlist URL

        Returns:
            list: 视频信息列表
        """
        print(f"📡 使用 yt-dlp 抓取...")

        try:
            import yt_dlp
        except ImportError:
            print("❌ 未安装 yt-dlp，请运行: pip install yt-dlp")
            return None

        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': True,  # 只提取元数据，不下载视频
                'ignoreerrors': True,
            }

            videos = []
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("  - 正在提取 Playlist 信息...")
                playlist_info = ydl.extract_info(playlist_url, download=False)

                if not playlist_info or 'entries' not in playlist_info:
                    print("❌ 无法获取 Playlist 信息")
                    return None

                total = len(playlist_info['entries'])
                print(f"  - 发现 {total} 个视频，开始获取详细信息...")

                for idx, entry in enumerate(playlist_info['entries'], 1):
                    if not entry:
                        continue

                    video_id = entry.get('id', '')
                    video_info = {
                        'videoId': video_id,
                        'url': f'https://www.youtube.com/watch?v={video_id}',
                        'title': entry.get('title', ''),
                        'description': entry.get('description', ''),
                        'channelTitle': entry.get('uploader', ''),
                        'channelId': entry.get('channel_id', ''),
                        'publishedAt': entry.get('upload_date', ''),
                        'thumbnails': {
                            'default': entry.get('thumbnail', ''),
                            'medium': entry.get('thumbnail', ''),
                            'high': entry.get('thumbnail', ''),
                        },
                        'position': idx - 1,
                        'duration': entry.get('duration', 0),
                        'viewCount': entry.get('view_count', 0)
                    }
                    videos.append(video_info)

                    if idx % 10 == 0:
                        print(f"    进度: {idx}/{total}")

                print(f"✅ yt-dlp 抓取完成，共获取 {len(videos)} 个视频")
                return videos

        except Exception as e:
            print(f"❌ yt-dlp 抓取出错: {str(e)}")
            return None

    def fetch_playlist(self, playlist_url, use_api_first=True):
        """
        混合方案抓取 Playlist

        Args:
            playlist_url: Playlist URL
            use_api_first: 是否优先使用 API（默认 True）

        Returns:
            list: 视频信息列表
        """
        print(f"\n{'='*60}")
        print(f"🎬 开始抓取 YouTube Playlist")
        print(f"{'='*60}\n")
        print(f"URL: {playlist_url}\n")

        # 提取 Playlist ID
        playlist_id = self.extract_playlist_id(playlist_url)
        if not playlist_id:
            print("❌ 无法解析 Playlist ID，请检查 URL 格式")
            return None

        print(f"Playlist ID: {playlist_id}\n")

        # 方案选择
        videos = None

        if use_api_first and self.api_key:
            # 优先使用 API
            videos = self.fetch_with_api(playlist_id)

            if videos is None:
                print("\n⚠️  API 方案失败，切换到 yt-dlp 方案...\n")
                videos = self.fetch_with_ytdlp(playlist_url)
        else:
            # 直接使用 yt-dlp
            videos = self.fetch_with_ytdlp(playlist_url)

            if videos is None and self.api_key:
                print("\n⚠️  yt-dlp 方案失败，切换到 API 方案...\n")
                videos = self.fetch_with_api(playlist_id)

        if videos:
            self.results = videos
            print(f"\n{'='*60}")
            print(f"✅ 抓取成功！共获取 {len(videos)} 个视频")
            print(f"{'='*60}\n")
        else:
            print(f"\n{'='*60}")
            print(f"❌ 所有方案均失败")
            print(f"{'='*60}\n")

        return videos

    def save_to_json(self, output_file, include_metadata=True):
        """
        保存结果到 JSON 文件

        Args:
            output_file: 输出文件路径
            include_metadata: 是否包含元数据（默认 True）
        """
        if not self.results:
            print("❌ 没有可保存的数据")
            return False

        try:
            data = {
                'metadata': {
                    'fetchedAt': datetime.now().isoformat(),
                    'totalVideos': len(self.results),
                    'fetchMethod': 'API' if self.api_key else 'yt-dlp'
                } if include_metadata else {},
                'videos': self.results
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            print(f"✅ 已保存到: {output_file}")
            print(f"   文件大小: {os.path.getsize(output_file) / 1024:.2f} KB")
            return True

        except Exception as e:
            print(f"❌ 保存失败: {str(e)}")
            return False

    def download_thumbnails(self, output_dir='thumbnails', quality='high'):
        """
        下载缩略图

        Args:
            output_dir: 输出目录
            quality: 缩略图质量 (default/medium/high/standard/maxres)
        """
        if not self.results:
            print("❌ 没有可下载的缩略图")
            return False
        if requests is None:
            print("❌ 未安装 requests，无法下载缩略图")
            return False

        os.makedirs(output_dir, exist_ok=True)
        print(f"\n📥 开始下载缩略图到: {output_dir}")
        print(f"   质量: {quality}\n")

        success_count = 0
        for idx, video in enumerate(self.results, 1):
            video_id = video['videoId']
            thumbnail_url = video['thumbnails'].get(quality, '')

            if not thumbnail_url:
                print(f"  [{idx}/{len(self.results)}] ⚠️  {video_id} - 无缩略图")
                continue

            try:
                response = requests.get(thumbnail_url, timeout=10)
                if response.status_code == 200:
                    # 确定文件扩展名
                    ext = 'jpg'
                    if 'image/png' in response.headers.get('Content-Type', ''):
                        ext = 'png'

                    file_path = os.path.join(output_dir, f"{video_id}.{ext}")
                    with open(file_path, 'wb') as f:
                        f.write(response.content)

                    success_count += 1
                    if idx % 10 == 0:
                        print(f"  进度: {idx}/{len(self.results)} - 成功: {success_count}")
                else:
                    print(f"  [{idx}/{len(self.results)}] ❌ {video_id} - HTTP {response.status_code}")

                # 避免请求过快
                time.sleep(0.3)

            except Exception as e:
                print(f"  [{idx}/{len(self.results)}] ❌ {video_id} - {str(e)}")

        print(f"\n✅ 缩略图下载完成: {success_count}/{len(self.results)}")
        return True

    def print_summary(self):
        """打印摘要信息"""
        if not self.results:
            print("❌ 没有数据")
            return

        print(f"\n{'='*60}")
        print(f"📊 数据摘要")
        print(f"{'='*60}\n")
        print(f"总视频数: {len(self.results)}")

        # 统计频道
        channels = {}
        for video in self.results:
            channel = video.get('channelTitle', 'Unknown')
            channels[channel] = channels.get(channel, 0) + 1

        print(f"\n频道分布:")
        for channel, count in sorted(channels.items(), key=lambda x: x[1], reverse=True)[:5]:
            print(f"  - {channel}: {count} 个视频")

        if len(channels) > 5:
            print(f"  - ... 还有 {len(channels) - 5} 个频道")

        # 显示前5个视频
        print(f"\n前 5 个视频:")
        for i, video in enumerate(self.results[:5], 1):
            print(f"  {i}. {video['title']}")
            print(f"     URL: {video['url']}")

        print(f"\n{'='*60}\n")


def main():
    """主函数 - 使用示例"""

    print("""
╔══════════════════════════════════════════════════════════╗
║     YouTube Playlist 视频信息抓取工具                    ║
║     支持混合方案：API + yt-dlp                          ║
╚══════════════════════════════════════════════════════════╝
    """)

    # ========================================
    # 配置区域 - 请根据实际情况修改
    # ========================================

    # YouTube API Key（可选，如果有请填写）
    API_KEY = DEFAULT_API_KEY  # 或通过环境变量 YOUTUBE_API_KEY 覆盖

    # Playlist URL（必填）
    PLAYLIST_URL = input("请输入 YouTube Playlist URL: ").strip()

    if not PLAYLIST_URL:
        print("❌ 请提供 Playlist URL")
        return

    # 是否下载缩略图
    DOWNLOAD_THUMBNAILS = input("是否下载缩略图？(y/n，默认n): ").strip().lower() == 'y'

    # ========================================
    # 开始抓取
    # ========================================

    # 创建抓取器
    fetcher = YouTubePlaylistFetcher(api_key=API_KEY if API_KEY else None)

    # 抓取 Playlist
    videos = fetcher.fetch_playlist(PLAYLIST_URL, use_api_first=True)

    if not videos:
        print("❌ 抓取失败")
        return

    # 打印摘要
    fetcher.print_summary()

    # 保存为 JSON
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = f'playlist_videos_{timestamp}.json'
    fetcher.save_to_json(output_file)

    # 下载缩略图（可选）
    if DOWNLOAD_THUMBNAILS:
        thumbnail_dir = f'thumbnails_{timestamp}'
        fetcher.download_thumbnails(output_dir=thumbnail_dir, quality='high')

    print("\n🎉 全部完成！\n")


if __name__ == '__main__':
    main()
