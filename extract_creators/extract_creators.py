#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
创作者信息提取和规范化工具
从 video_info JSON 中提取并规范化创作者信息
"""

import os
import sys
import json
import argparse
from datetime import datetime
from typing import Dict, List, Optional

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import CONFIG
from extractors.pattern_matcher import PatternMatcher
from extractors.text_normalizer import TextNormalizer
from validators.sekai_validator import SekaiValidator


class CreatorExtractor:
    """创作者信息提取器"""

    def __init__(self, config: Dict):
        """初始化提取器"""
        self.config = config
        self.pattern_matcher = PatternMatcher()
        self.normalizer = TextNormalizer()
        self.sekai_validator = SekaiValidator(config['sekai_music_file'])

        # 统计信息
        self.stats = {
            'total': 0,
            'full_extracted': 0,      # 完整提取（作词+作曲+编曲）
            'partial_extracted': 0,   # 部分提取
            'manual_review': 0,       # 需要人工审核
            'validated': 0,           # 与Sekai数据一致
            'conflicts': 0,           # 与Sekai数据冲突
        }

        # 需要人工审核的条目
        self.manual_review_items = []

    def load_video_info(self, video_info_file: str) -> List[Dict]:
        """加载视频信息JSON文件"""
        print(f"\n[INFO] 加载视频信息: {video_info_file}")

        with open(video_info_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

        videos = data.get('videos', [])
        print(f"[OK] 已加载 {len(videos)} 个视频")
        return videos

    def extract_from_description(self, description: str) -> Dict[str, Optional[str]]:
        """从description中提取创作者信息"""
        result = {
            'lyricist': None,
            'composer': None,
            'arranger': None,
            'illustrator': None,
            'videoDirector': None,
        }

        if not description:
            return result

        # 优先级1: 检查全能型模式（作词・作曲・编曲）
        all_in_one = self.pattern_matcher.match_all_in_one(description)
        if all_in_one:
            result['lyricist'] = all_in_one
            result['composer'] = all_in_one
            result['arranger'] = all_in_one
            return result

        # 优先级2: 检查组合模式（作词・作曲）
        lyricist_composer = self.pattern_matcher.match_lyricist_composer(description)
        if lyricist_composer:
            result['lyricist'] = lyricist_composer
            result['composer'] = lyricist_composer

        # 优先级3: 分别匹配各个字段
        if not result['lyricist']:
            result['lyricist'] = self.pattern_matcher.match_lyricist(description)

        if not result['composer']:
            result['composer'] = self.pattern_matcher.match_composer(description)

        if not result['arranger']:
            result['arranger'] = self.pattern_matcher.match_arranger(description)

        # 可选字段
        result['illustrator'] = self.pattern_matcher.match_illustrator(description)
        result['videoDirector'] = self.pattern_matcher.match_video_director(description)

        return result

    def extract_from_uploader(self, uploader: str) -> Optional[str]:
        """从uploader中提取创作者信息（作为fallback）"""
        if not uploader:
            return None

        # 清理常见的后缀
        import re
        cleaned = re.sub(r'\s*(Official|Channel|チャンネル|公式).*$', '', uploader, flags=re.IGNORECASE)
        return cleaned.strip()

    def extract_creators(self, video: Dict) -> Dict:
        """提取单个视频的创作者信息"""
        metadata = video.get('metadata', {})
        music_id = video.get('musicId')

        # 从description提取
        creators = self.extract_from_description(metadata.get('description', ''))

        # 从uploader提取（fallback）
        if not creators['composer']:
            uploader_composer = self.extract_from_uploader(metadata.get('uploader', ''))
            if uploader_composer:
                creators['composer'] = uploader_composer
                creators['_source'] = 'uploader_fallback'

        # 规范化文本
        for key in ['lyricist', 'composer', 'arranger', 'illustrator', 'videoDirector']:
            if creators.get(key):
                creators[key] = self.normalizer.normalize(creators[key])

        # 与Sekai Viewer数据验证
        sekai_data = self.sekai_validator.get_music_creators(music_id)
        validation_result = self.sekai_validator.validate(creators, sekai_data)

        # 构建结果
        result = {
            'id': video.get('id'),
            'musicId': music_id,
            'videoId': video.get('videoId'),
            'platform': video.get('platform'),
            'creators': creators,
            'sekaiData': sekai_data,
            'validation': validation_result,
        }

        # 判断是否需要人工审核
        if validation_result['needsReview']:
            self.manual_review_items.append(result)

        return result

    def process_all(self, videos: List[Dict]) -> List[Dict]:
        """批量处理所有视频"""
        print(f"\n[INFO] 开始提取创作者信息...")
        results = []

        for video in videos:
            result = self.extract_creators(video)
            results.append(result)

            # 更新统计
            self.stats['total'] += 1

            creators = result['creators']
            extracted_count = sum(1 for v in [creators.get('lyricist'), creators.get('composer'), creators.get('arranger')] if v)

            if extracted_count == 3:
                self.stats['full_extracted'] += 1
            elif extracted_count > 0:
                self.stats['partial_extracted'] += 1

            if result['validation']['needsReview']:
                self.stats['manual_review'] += 1

            if result['validation']['isValid']:
                self.stats['validated'] += 1

            if result['validation']['conflicts']:
                self.stats['conflicts'] += 1

        print(f"[OK] 提取完成: {len(results)} 个视频")
        return results

    def save_results(self, results: List[Dict], output_dir: str):
        """保存结果"""
        os.makedirs(output_dir, exist_ok=True)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        # 主输出文件
        output_file = os.path.join(output_dir, f'creators_extracted_{timestamp}.json')
        output_data = {
            'metadata': {
                'extractedAt': datetime.now().isoformat(),
                'totalVideos': self.stats['total'],
                'fullExtracted': self.stats['full_extracted'],
                'partialExtracted': self.stats['partial_extracted'],
                'manualReview': self.stats['manual_review'],
                'validated': self.stats['validated'],
                'conflicts': self.stats['conflicts'],
            },
            'results': results,
        }

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)

        print(f"\n[SAVE] 结果已保存: {output_file}")

        # 需要人工审核的文件
        if self.manual_review_items:
            review_file = os.path.join(output_dir, f'manual_review_{timestamp}.json')
            with open(review_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'metadata': {
                        'totalItems': len(self.manual_review_items),
                        'extractedAt': datetime.now().isoformat(),
                    },
                    'items': self.manual_review_items,
                }, f, ensure_ascii=False, indent=2)

            print(f"[WARN] 需要人工审核: {review_file} ({len(self.manual_review_items)} 个)")

    def print_summary(self):
        """打印统计摘要"""
        print(f"\n{'=' * 60}")
        print(f"{' ' * 25}提取完成")
        print(f"{'=' * 60}")

        print(f"\n[统计信息]")
        print(f"   总视频数: {self.stats['total']}")
        print(f"   [OK] 完整提取: {self.stats['full_extracted']} ({self.stats['full_extracted']/self.stats['total']*100:.1f}%)")
        print(f"   [PARTIAL] 部分提取: {self.stats['partial_extracted']} ({self.stats['partial_extracted']/self.stats['total']*100:.1f}%)")
        print(f"   [REVIEW] 需要审核: {self.stats['manual_review']} ({self.stats['manual_review']/self.stats['total']*100:.1f}%)")
        print(f"   [VALID] 验证通过: {self.stats['validated']} ({self.stats['validated']/self.stats['total']*100:.1f}%)")
        print(f"   [CONFLICT] 数据冲突: {self.stats['conflicts']} ({self.stats['conflicts']/self.stats['total']*100:.1f}%)")
        print(f"\n[SUCCESS] 全部完成！")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='从视频信息中提取创作者信息',
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        '--video-info',
        help='视频信息文件路径',
        default=None
    )

    args = parser.parse_args()

    # 打印标题
    print(f"\n{'=' * 60}")
    print(f"{' ' * 20}创作者信息提取工具")
    print(f"{'=' * 60}")

    # 创建提取器
    extractor = CreatorExtractor(CONFIG)

    # 加载视频信息
    video_info_file = args.video_info or CONFIG['video_info_file']
    videos = extractor.load_video_info(video_info_file)

    # 批量提取
    results = extractor.process_all(videos)

    # 保存结果
    extractor.save_results(results, CONFIG['output_dir'])

    # 打印摘要
    extractor.print_summary()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] 用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n[ERROR] 发生错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
