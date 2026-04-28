#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MV 版本关联工具
通过 musicId 将同一首歌的多个 MV 版本关联起来
"""

import json
import re
from datetime import datetime
from collections import defaultdict
from difflib import SequenceMatcher


class MVVersionLinker:
    """MV 版本关联器"""

    # 版本类型定义
    VERSION_TYPES = {
        "game_original": "游戏内原版",
        "game_anniversary": "周年纪念版",
        "game_event": "活动限定版",
        "original_artist": "原作者官方版",
        "movie_version": "电影版",
        "sekai_version": "SEKAI版",
        "unit_version": "组合版本",
        "character_version": "角色版本",
        "collaboration": "联动版本",
        "other": "其他版本"
    }

    def __init__(self, all_musics_path, youtube_playlist_path):
        """
        初始化

        Args:
            all_musics_path: all_musics.json 路径
            youtube_playlist_path: YouTube Playlist 抓取结果路径
        """
        self.all_musics_path = all_musics_path
        self.youtube_playlist_path = youtube_playlist_path
        self.musics = []
        self.youtube_videos = []
        self.linked_data = []

    def load_data(self):
        """加载数据"""
        print("📂 加载数据...")

        # 加载 all_musics.json
        try:
            with open(self.all_musics_path, 'r', encoding='utf-8') as f:
                self.musics = json.load(f)
            print(f"   ✓ 加载了 {len(self.musics)} 首歌曲")
        except Exception as e:
            print(f"   ❌ 加载 all_musics.json 失败: {e}")
            return False

        # 加载 YouTube Playlist 数据
        try:
            with open(self.youtube_playlist_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.youtube_videos = data.get('videos', [])
            print(f"   ✓ 加载了 {len(self.youtube_videos)} 个 YouTube 视频")
        except Exception as e:
            print(f"   ❌ 加载 YouTube 数据失败: {e}")
            return False

        return True

    def normalize_title(self, title):
        """标准化标题，用于匹配"""
        # 移除特殊字符和空格
        title = re.sub(r'[\s\-_・×]', '', title.lower())
        # 移除版本标识
        title = re.sub(r'(mv|ver\.?|version|映像|動画)', '', title, flags=re.IGNORECASE)
        return title

    def calculate_similarity(self, str1, str2):
        """计算字符串相似度"""
        return SequenceMatcher(None, str1, str2).ratio()

    def detect_version_type(self, video_title, video_description):
        """
        检测 MV 版本类型

        Args:
            video_title: 视频标题
            video_description: 视频描述

        Returns:
            str: 版本类型
        """
        title_lower = video_title.lower()
        desc_lower = video_description.lower()

        # 检测规则
        if '劇場版' in video_title or '映画' in video_title or 'movie' in title_lower:
            return "movie_version"
        elif '周年' in video_title or 'anniversary' in title_lower:
            return "game_anniversary"
        elif 'セカイ' in video_title and 'ver' in title_lower:
            return "sekai_version"
        elif any(unit in video_title for unit in ['Leo/need', 'MORE MORE JUMP', 'Vivid BAD SQUAD', 'ワンダーランズ×ショウタイム', '25時、ナイトコードで']):
            return "unit_version"
        elif 'イベント' in video_title or 'event' in title_lower:
            return "game_event"
        elif '×' in video_title or 'collaboration' in title_lower or 'collab' in title_lower:
            return "collaboration"
        elif 'プロセカ' not in video_title and 'プロジェクトセカイ' not in video_title:
            return "original_artist"
        else:
            return "game_original"

    def extract_version_name(self, video_title):
        """
        从标题提取版本名称

        Args:
            video_title: 视频标题

        Returns:
            str: 版本名称
        """
        # 匹配各种版本标识
        patterns = [
            r'「(.+?)」\s*ver',
            r'（(.+?)）\s*ver',
            r'【(.+?)】',
            r'\((.+?)\)\s*ver',
            r'(.+?)\s*ver\.',
            r'×\s*(.+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, video_title, re.IGNORECASE)
            if match:
                return match.group(1).strip()

        # 如果没有明确的版本标识，返回完整标题
        return video_title

    def extract_creators_from_description(self, description):
        """
        从描述中提取创作者信息

        Args:
            description: 视频描述

        Returns:
            dict: 创作者信息
        """
        creators = {}

        # 常见的创作者标识模式
        patterns = {
            'animation_studio': [
                r'アニメーション制作[：:]\s*(.+?)(?:\n|$)',
                r'制作[：:]\s*(.+?)(?:\n|$)',
            ],
            'director': [
                r'監督[：:]\s*(.+?)(?:\n|$)',
                r'演出[：:]\s*(.+?)(?:\n|$)',
            ],
            'animator': [
                r'アニメーション[：:]\s*(.+?)(?:\n|$)',
                r'2DMV[：:]\s*(.+?)(?:\n|$)',
                r'映像[：:]\s*(.+?)(?:\n|$)',
                r'動画[：:]\s*(.+?)(?:\n|$)',
                r'Movie[：:]\s*(.+?)(?:\n|$)',
            ],
            'illustrator': [
                r'イラスト[：:]\s*(.+?)(?:\n|$)',
                r'Illustration[：:]\s*(.+?)(?:\n|$)',
            ],
            'lyric_designer': [
                r'リリックデザイン[：:]\s*(.+?)(?:\n|$)',
            ]
        }

        for creator_type, pattern_list in patterns.items():
            for pattern in pattern_list:
                matches = re.findall(pattern, description, re.MULTILINE | re.IGNORECASE)
                if matches:
                    creators[creator_type] = matches[0].strip()
                    break

        return creators

    def link_versions(self, similarity_threshold=0.6):
        """
        关联 MV 版本

        Args:
            similarity_threshold: 标题相似度阈值（0-1）

        Returns:
            list: 关联后的数据
        """
        print(f"\n🔗 开始关联 MV 版本（相似度阈值: {similarity_threshold}）...\n")

        # 为每首歌创建一个 MV 版本列表
        music_mv_map = defaultdict(list)
        matched_videos = set()

        for music in self.musics:
            music_id = music['id']
            music_title = music['title']
            music_title_normalized = self.normalize_title(music_title)

            print(f"🎵 处理: {music_title} (ID: {music_id})")

            # 首先尝试通过 originalVideoLink 精确匹配
            original_link = music.get('originalVideoLink', '')

            for video in self.youtube_videos:
                if video['url'] in matched_videos:
                    continue

                video_title = video['title']
                video_title_normalized = self.normalize_title(video_title)

                # 计算相似度
                similarity = self.calculate_similarity(music_title_normalized, video_title_normalized)

                # 精确匹配或高相似度匹配
                is_match = False
                match_reason = ""

                if original_link and video['url'] == original_link:
                    is_match = True
                    match_reason = "URL精确匹配"
                elif similarity >= similarity_threshold:
                    is_match = True
                    match_reason = f"标题相似度 {similarity:.2%}"
                elif music_title in video_title or video_title in music_title:
                    is_match = True
                    match_reason = "标题包含匹配"

                if is_match:
                    # 检测版本类型
                    version_type = self.detect_version_type(video_title, video.get('description', ''))
                    version_name = self.extract_version_name(video_title)

                    # 提取创作者信息
                    creators = self.extract_creators_from_description(video.get('description', ''))

                    # 构建 MV 版本信息
                    mv_version = {
                        'versionId': f"mv_{music_id}_{len(music_mv_map[music_id]) + 1:03d}",
                        'versionName': version_name,
                        'versionType': version_type,
                        'versionTypeDisplay': self.VERSION_TYPES.get(version_type, version_type),
                        'priority': len(music_mv_map[music_id]) + 1,
                        'youtube': {
                            'videoId': video['videoId'],
                            'url': video['url'],
                            'title': video['title'],
                            'description': video.get('description', ''),
                            'channelTitle': video.get('channelTitle', ''),
                            'channelId': video.get('channelId', ''),
                            'publishedAt': video.get('publishedAt', ''),
                            'thumbnails': video.get('thumbnails', {}),
                        },
                        'creators': creators,
                        'matchReason': match_reason,
                        'similarity': similarity
                    }

                    music_mv_map[music_id].append(mv_version)
                    matched_videos.add(video['url'])

                    print(f"   ✓ 匹配: {video_title}")
                    print(f"     - 版本: {version_name}")
                    print(f"     - 类型: {self.VERSION_TYPES.get(version_type, version_type)}")
                    print(f"     - 原因: {match_reason}")
                    if creators:
                        print(f"     - 创作者: {', '.join([f'{k}={v}' for k,v in creators.items()])}")

        # 构建最终数据结构
        print(f"\n📊 构建最终数据结构...\n")

        for music in self.musics:
            music_id = music['id']
            mv_versions = music_mv_map.get(music_id, [])

            # 按优先级排序（游戏官方版本优先）
            mv_versions.sort(key=lambda x: (
                0 if x['versionType'] == 'game_original' else
                1 if x['versionType'] == 'game_anniversary' else
                2 if x['versionType'] == 'sekai_version' else
                3 if x['versionType'] == 'original_artist' else
                4
            ))

            # 重新分配优先级
            for idx, mv in enumerate(mv_versions, 1):
                mv['priority'] = idx

            linked_music = {
                'musicId': music_id,
                'title': music['title'],
                'titlePronunciation': music.get('pronunciation', ''),
                'artist': {
                    'composer': music.get('composer', ''),
                    'lyricist': music.get('lyricist', ''),
                    'arranger': music.get('arranger', ''),
                },
                'releaseInfo': {
                    'publishedAt': music.get('publishedAt', ''),
                    'releasedAt': music.get('releasedAt', ''),
                    'isNewlyWrittenMusic': music.get('isNewlyWrittenMusic', False),
                },
                'mvVersions': mv_versions,
                'statistics': {
                    'totalMvVersions': len(mv_versions),
                    'hasOriginalArtistMv': any(mv['versionType'] == 'original_artist' for mv in mv_versions),
                    'hasMovieVersion': any(mv['versionType'] == 'movie_version' for mv in mv_versions),
                }
            }

            self.linked_data.append(linked_music)

        return self.linked_data

    def print_statistics(self):
        """打印统计信息"""
        print(f"\n{'='*60}")
        print(f"📊 关联统计")
        print(f"{'='*60}\n")

        total_musics = len(self.linked_data)
        musics_with_mv = sum(1 for m in self.linked_data if m['statistics']['totalMvVersions'] > 0)
        musics_with_multiple_mv = sum(1 for m in self.linked_data if m['statistics']['totalMvVersions'] > 1)
        total_mv_versions = sum(m['statistics']['totalMvVersions'] for m in self.linked_data)

        print(f"总歌曲数: {total_musics}")
        print(f"有 MV 的歌曲: {musics_with_mv} ({musics_with_mv/total_musics*100:.1f}%)")
        print(f"有多版本 MV 的歌曲: {musics_with_multiple_mv} ({musics_with_multiple_mv/total_musics*100:.1f}%)")
        print(f"MV 版本总数: {total_mv_versions}")
        print(f"平均每首歌 MV 数: {total_mv_versions/total_musics:.2f}")

        # 版本类型统计
        version_type_count = defaultdict(int)
        for music in self.linked_data:
            for mv in music['mvVersions']:
                version_type_count[mv['versionTypeDisplay']] += 1

        print(f"\nMV 版本类型分布:")
        for vtype, count in sorted(version_type_count.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {vtype}: {count}")

        # 多版本歌曲列表
        print(f"\n多版本 MV 歌曲 (前10):")
        multi_mv_songs = [(m['title'], m['statistics']['totalMvVersions'])
                          for m in self.linked_data
                          if m['statistics']['totalMvVersions'] > 1]
        multi_mv_songs.sort(key=lambda x: x[1], reverse=True)

        for title, count in multi_mv_songs[:10]:
            print(f"  - {title}: {count} 个版本")

        print(f"\n{'='*60}\n")

    def save_to_json(self, output_file, format_type='nested'):
        """
        保存到 JSON

        Args:
            output_file: 输出文件路径
            format_type: 数据格式 ('nested' 或 'relational')
        """
        print(f"💾 保存数据到: {output_file}")

        try:
            if format_type == 'nested':
                # 嵌套结构
                data = {
                    'metadata': {
                        'generatedAt': datetime.now().isoformat(),
                        'totalMusics': len(self.linked_data),
                        'totalMvVersions': sum(m['statistics']['totalMvVersions'] for m in self.linked_data),
                        'dataFormat': 'nested',
                        'description': '通过 musicId 关联的 MV 版本数据（嵌套结构）'
                    },
                    'musics': self.linked_data
                }
            else:
                # 关系型结构
                mv_versions_flat = []
                for music in self.linked_data:
                    for mv in music['mvVersions']:
                        mv_flat = {
                            'musicId': music['musicId'],
                            **mv
                        }
                        mv_versions_flat.append(mv_flat)

                data = {
                    'metadata': {
                        'generatedAt': datetime.now().isoformat(),
                        'totalMusics': len(self.linked_data),
                        'totalMvVersions': len(mv_versions_flat),
                        'dataFormat': 'relational',
                        'description': '通过 musicId 关联的 MV 版本数据（关系型结构）'
                    },
                    'musics': [{
                        'musicId': m['musicId'],
                        'title': m['title'],
                        'titlePronunciation': m['titlePronunciation'],
                        'artist': m['artist'],
                        'releaseInfo': m['releaseInfo'],
                        'statistics': m['statistics']
                    } for m in self.linked_data],
                    'mvVersions': mv_versions_flat
                }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            import os
            file_size = os.path.getsize(output_file) / 1024
            print(f"   ✓ 保存成功")
            print(f"   文件大小: {file_size:.2f} KB")

        except Exception as e:
            print(f"   ❌ 保存失败: {e}")


def main():
    """主函数"""

    print("""
╔══════════════════════════════════════════════════════════╗
║        MV 版本关联工具 - 通过 musicId 关联              ║
╚══════════════════════════════════════════════════════════╝
    """)

    # 配置文件路径
    ALL_MUSICS_PATH = input("请输入 all_musics.json 路径: ").strip().strip('"')
    YOUTUBE_PLAYLIST_PATH = input("请输入 YouTube Playlist JSON 路径: ").strip().strip('"')

    if not ALL_MUSICS_PATH or not YOUTUBE_PLAYLIST_PATH:
        print("❌ 请提供必要的文件路径")
        return

    # 创建关联器
    linker = MVVersionLinker(ALL_MUSICS_PATH, YOUTUBE_PLAYLIST_PATH)

    # 加载数据
    if not linker.load_data():
        return

    # 关联版本
    linker.link_versions(similarity_threshold=0.6)

    # 打印统计
    linker.print_statistics()

    # 保存结果
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # 保存嵌套结构
    output_nested = f'linked_mv_versions_nested_{timestamp}.json'
    linker.save_to_json(output_nested, format_type='nested')

    # 保存关系型结构
    output_relational = f'linked_mv_versions_relational_{timestamp}.json'
    linker.save_to_json(output_relational, format_type='relational')

    print("\n🎉 全部完成！\n")
    print("生成的文件:")
    print(f"  1. {output_nested} (嵌套结构，推荐用于前端展示)")
    print(f"  2. {output_relational} (关系型结构，推荐用于数据库)")


if __name__ == '__main__':
    main()
