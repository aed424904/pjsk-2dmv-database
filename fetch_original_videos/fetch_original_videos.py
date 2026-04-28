#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
原曲视频信息抓取工具
使用 yt-dlp 从 musicOriginals.json 抓取 YouTube 和 Niconico 视频的详细信息
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import List, Dict
from tqdm import tqdm

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from utils.video_fetcher import VideoFetcher
from utils.cache_manager import CacheManager
from utils.error_handler import RetryConfig


class OriginalVideoFetcher:
    """原曲视频信息抓取器"""

    def __init__(self, args):
        """初始化"""
        self.args = args
        self.source_file = args.source or CONFIG['source_file']
        self.output_dir = args.output_dir or CONFIG['output_dir']
        self.batch_size = args.batch_size or CONFIG['batch_size']

        # 确保输出目录存在
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs(CONFIG['log_dir'], exist_ok=True)

        # 初始化视频抓取器
        retry_config = RetryConfig(**CONFIG['retry'])
        self.fetcher = VideoFetcher(
            ytdlp_opts=CONFIG['ytdlp_opts'],
            use_cache=not args.no_cache,
            cache_dir=CONFIG['cache_dir'],
            cache_expiry_days=CONFIG['cache_expiry_days'],
            retry_config=retry_config,
            proxy=args.proxy or CONFIG['proxy']
        )

        # 初始化缓存管理器（用于统计）
        self.cache_manager = CacheManager(CONFIG['cache_dir'], CONFIG['cache_expiry_days'])

        # 结果存储
        self.results = []
        self.failed_videos = []

    def load_source_data(self) -> List[Dict]:
        """加载数据源"""
        print(f"\n📂 加载数据源: {self.source_file}")

        if not os.path.exists(self.source_file):
            print(f"❌ 数据源文件不存在: {self.source_file}")
            sys.exit(1)

        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                data = json.load(f)

            print(f"✅ 已加载 {len(data)} 个视频链接")
            return data

        except Exception as e:
            print(f"❌ 加载数据源失败: {e}")
            sys.exit(1)

    def filter_videos(self, videos: List[Dict]) -> List[Dict]:
        """筛选需要处理的视频"""
        # 如果指定了 --retry-failed，只处理之前失败的视频
        if self.args.retry_failed:
            failed_file = os.path.join(self.output_dir, 'failed_videos.json')
            if os.path.exists(failed_file):
                with open(failed_file, 'r', encoding='utf-8') as f:
                    failed_data = json.load(f)
                    failed_ids = {v['id'] for v in failed_data.get('failed', [])}
                    videos = [v for v in videos if v['id'] in failed_ids]
                    print(f"🔄 重试模式: 将处理 {len(videos)} 个失败的视频")
            else:
                print(f"⚠️  未找到失败记录文件")
                return []

        # 如果启用了 --resume，跳过已处理的视频
        if self.args.resume:
            progress_file = os.path.join(self.output_dir, 'progress.json')
            if os.path.exists(progress_file):
                with open(progress_file, 'r', encoding='utf-8') as f:
                    progress = json.load(f)
                    processed_ids = set(progress.get('processedVideoIds', []))
                    videos = [v for v in videos if v['id'] not in processed_ids]
                    print(f"▶️  继续模式: 跳过已处理，还需处理 {len(videos)} 个视频")

        return videos

    def fetch_all(self, videos: List[Dict]):
        """批量抓取所有视频"""
        total = len(videos)
        if total == 0:
            print("⚠️  没有需要处理的视频")
            return

        print(f"\n🚀 开始抓取 {total} 个视频...")
        print(f"📦 批次大小: {self.batch_size}")
        print(f"⚙️  并发数: {CONFIG['max_workers']}")
        print(f"💾 缓存: {'启用' if not self.args.no_cache else '禁用'}")

        # 清理过期缓存
        if not self.args.no_cache:
            cleared = self.cache_manager.clear_expired()
            if cleared > 0:
                print(f"🧹 已清理 {cleared} 个过期缓存")

        # 使用 tqdm 显示进度
        with tqdm(total=total, desc="抓取进度", unit="视频") as pbar:
            def progress_callback(current, batch_total, result):
                # 更新进度条
                pbar.update(1)

                # 显示当前处理的视频
                status_emoji = "✅" if result['status'] == 'success' else "❌"
                video_id = result.get('videoId', 'unknown')
                pbar.set_postfix({
                    'ID': video_id,
                    'Status': status_emoji
                })

                # 保存结果
                self.results.append(result)

                # 记录失败的视频
                if result['status'] == 'failed':
                    self.failed_videos.append(result)

            # 批量处理
            num_batches = (total + self.batch_size - 1) // self.batch_size

            for batch_idx in range(num_batches):
                start_idx = batch_idx * self.batch_size
                end_idx = min(start_idx + self.batch_size, total)
                batch = videos[start_idx:end_idx]

                # 获取平台特定的延迟
                delay = CONFIG['delay_between_requests']

                # 处理批次
                self.fetcher.fetch_batch(batch, delay=delay, progress_callback=progress_callback)

                # 定期保存进度
                if batch_idx % 5 == 0:
                    self._save_progress()

        print("\n✅ 抓取完成!")

    def _save_progress(self):
        """保存进度"""
        progress_file = os.path.join(self.output_dir, 'progress.json')
        processed_ids = [r['id'] for r in self.results]

        progress = {
            'lastUpdated': datetime.now().isoformat(),
            'processedVideoIds': processed_ids,
            'totalProcessed': len(processed_ids),
        }

        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(progress, f, ensure_ascii=False, indent=2)

    def save_results(self):
        """保存结果"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 统计信息
        stats = self.fetcher.get_stats()
        success_results = [r for r in self.results if r['status'] == 'success']
        failed_results = [r for r in self.results if r['status'] == 'failed']

        # 平台分布统计
        platform_stats = {}
        for result in self.results:
            platform = result.get('platform', 'unknown')
            if platform not in platform_stats:
                platform_stats[platform] = {'total': 0, 'success': 0, 'failed': 0}

            platform_stats[platform]['total'] += 1
            if result['status'] == 'success':
                platform_stats[platform]['success'] += 1
            else:
                platform_stats[platform]['failed'] += 1

        # 主输出文件
        output_file = os.path.join(self.output_dir, f'video_info_{timestamp}.json')
        output_data = {
            'metadata': {
                'fetchedAt': datetime.now().isoformat(),
                'source': self.source_file,
                'totalVideos': stats['total'],
                'successCount': stats['success'],
                'failedCount': stats['failed'],
                'cachedCount': stats['cached'],
                'platformDistribution': platform_stats,
            },
            'videos': self.results,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n📁 结果已保存:")
        print(f"   ✅ {output_file} ({len(success_results)} 个成功)")

        # 失败记录文件
        if failed_results:
            failed_file = os.path.join(self.output_dir, 'failed_videos.json')
            failed_data = {
                'metadata': {
                    'lastUpdated': datetime.now().isoformat(),
                    'totalFailed': len(failed_results),
                },
                'failed': failed_results,
            }

            with open(failed_file, 'w', encoding='utf-8') as f:
                json.dump(failed_data, f, ensure_ascii=False, indent=2)

            print(f"   ❌ {failed_file} ({len(failed_results)} 个失败)")

    def print_summary(self):
        """打印统计摘要"""
        stats = self.fetcher.get_stats()

        print(f"\n╔{'═' * 58}╗")
        print(f"║{' ' * 20}抓取完成{' ' * 26}║")
        print(f"╚{'═' * 58}╝")

        print(f"\n📊 统计信息:")
        print(f"   总视频数: {stats['total']}")
        print(f"   ✅ 成功: {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
        print(f"   ❌ 失败: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
        print(f"   💾 缓存: {stats['cached']}")

        # 平台统计
        platform_counts = {}
        for result in self.results:
            platform = result.get('platform', 'unknown')
            status = result['status']
            if platform not in platform_counts:
                platform_counts[platform] = {'success': 0, 'failed': 0}
            platform_counts[platform][status] += 1

        print(f"\n   平台统计:")
        for platform, counts in platform_counts.items():
            total = counts['success'] + counts['failed']
            success_rate = counts['success'] / total * 100 if total > 0 else 0
            print(f"   - {platform.capitalize()}: 成功 {counts['success']}/{total} ({success_rate:.1f}%)")

        print(f"\n🎉 全部完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='抓取 MV 原曲视频信息（支持 YouTube 和 Niconico）',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 全量抓取
  python fetch_original_videos.py

  # 从断点继续
  python fetch_original_videos.py --resume

  # 重试失败的视频
  python fetch_original_videos.py --retry-failed

  # 使用代理
  python fetch_original_videos.py --proxy http://127.0.0.1:7890

  # 不使用缓存
  python fetch_original_videos.py --no-cache
        """
    )

    parser.add_argument(
        '--source',
        help='数据源文件路径',
        default=None
    )
    parser.add_argument(
        '--output-dir',
        help='输出目录',
        default=None
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        help='每批处理的视频数量',
        default=None
    )
    parser.add_argument(
        '--resume',
        action='store_true',
        help='从上次中断处继续'
    )
    parser.add_argument(
        '--retry-failed',
        action='store_true',
        help='重试之前失败的视频'
    )
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='不使用缓存'
    )
    parser.add_argument(
        '--proxy',
        type=str,
        help='代理服务器地址（如 http://127.0.0.1:7890）',
        default=None
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='限制处理的视频数量（用于测试）',
        default=None
    )

    args = parser.parse_args()

    # 打印标题
    print(f"\n╔{'═' * 58}╗")
    print(f"║{' ' * 15}原曲视频信息抓取工具{' ' * 21}║")
    print(f"║{' ' * 15}支持平台：YouTube + Niconico{' ' * 13}║")
    print(f"╚{'═' * 58}╝")

    # 创建抓取器
    fetcher = OriginalVideoFetcher(args)

    # 加载数据源
    videos = fetcher.load_source_data()

    # 筛选视频
    videos = fetcher.filter_videos(videos)

    # 限制数量（测试用）
    if args.limit:
        videos = videos[:args.limit]
        print(f"⚠️  测试模式: 限制处理 {args.limit} 个视频")

    # 抓取
    fetcher.fetch_all(videos)

    # 保存结果
    fetcher.save_results()

    # 打印摘要
    fetcher.print_summary()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断，正在保存进度...")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
