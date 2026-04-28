#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Sekai 音乐数据提取工具
从master数据库中提取音乐相关信息并整合
"""

import json
import os
from typing import List, Dict, Any
from datetime import datetime

class MusicDataExtractor:
    """音乐数据提取器"""

    def __init__(self, data_dir: str):
        """
        初始化提取器

        Args:
            data_dir: master数据库所在目录
        """
        self.data_dir = data_dir
        self.musics = []
        self.music_vocals = []
        self.music_difficulties = []
        self.music_tags = []
        self.game_characters = []
        self.music_video_characters = []
        self.music_asset_variants = []
        self.music_originals = []

    def load_json(self, filename: str) -> List[Dict]:
        """加载JSON文件"""
        filepath = os.path.join(self.data_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ 加载 {filename} 失败: {e}")
            return []

    def load_all_data(self):
        """加载所有音乐相关数据"""
        print("📁 开始加载音乐数据...")
        self.musics = self.load_json('musics.json')
        self.music_vocals = self.load_json('musicVocals.json')
        self.music_difficulties = self.load_json('musicDifficulties.json')
        self.music_tags = self.load_json('musicTags.json')
        self.game_characters = self.load_json('gameCharacters.json')
        self.music_video_characters = self.load_json('musicVideoCharacters.json')
        self.music_asset_variants = self.load_json('musicAssetVariants.json')
        self.music_originals = self.load_json('musicOriginals.json')

        print(f"✅ 加载完成:")
        print(f"   - 音乐: {len(self.musics)} 首")
        print(f"   - 演唱版本: {len(self.music_vocals)} 个")
        print(f"   - 难度数据: {len(self.music_difficulties)} 条")
        print(f"   - 标签数据: {len(self.music_tags)} 条")
        print(f"   - 角色数据: {len(self.game_characters)} 个")
        print(f"   - MV角色: {len(self.music_video_characters)} 条")
        print(f"   - MV资源变体: {len(self.music_asset_variants)} 条")
        print(f"   - 原曲MV链接: {len(self.music_originals)} 条")

    def extract_music_list(self, filter_opts: Dict[str, Any] = None) -> List[Dict]:
        """
        提取音乐列表（整合所有相关数据）

        Args:
            filter_opts: 过滤选项
                - music_ids: 指定要提取的音乐ID列表
                - limit: 限制提取数量
                - tags: 只提取包含特定标签的音乐
                - min_level: 最低难度等级

        Returns:
            整合后的音乐数据列表
        """
        filter_opts = filter_opts or {}

        # 构建角色ID到名字的映射
        character_map = {}
        for char in self.game_characters:
            char_id = char['id']
            first_name = char.get('firstName', '')
            given_name = char.get('givenName', '')
            character_map[char_id] = {
                'id': char_id,
                'name': f"{first_name} {given_name}".strip(),
                'firstName': first_name,
                'givenName': given_name,
                'unit': char.get('unit', ''),
                'gender': char.get('gender', '')
            }

        # 构建索引以便快速查找
        vocals_by_music = {}
        for vocal in self.music_vocals:
            music_id = vocal['musicId']
            vocal_id = vocal['id']

            # 添加演唱者详细信息
            vocal_with_singers = vocal.copy()
            singers = []
            for char_info in vocal.get('characters', []):
                char_id = char_info.get('characterId')
                if char_id in character_map:
                    singer = character_map[char_id].copy()
                    singer['characterType'] = char_info.get('characterType', '')
                    singers.append(singer)
            vocal_with_singers['singers'] = singers

            # 查找该vocal的MV资源变体
            mv_variants = []
            for variant in self.music_asset_variants:
                if variant.get('musicVocalId') == vocal_id and variant.get('musicAssetType') == 'mv':
                    mv_variants.append({
                        'id': variant['id'],
                        'assetbundleName': variant.get('assetbundleName', '')
                    })
            vocal_with_singers['mvVariants'] = mv_variants

            if music_id not in vocals_by_music:
                vocals_by_music[music_id] = []
            vocals_by_music[music_id].append(vocal_with_singers)

        # 构建MV角色信息（默认MV中的舞蹈角色）
        mv_characters_by_music = {}
        for mv_char in self.music_video_characters:
            music_id = mv_char['musicId']
            if music_id not in mv_characters_by_music:
                mv_characters_by_music[music_id] = []

            char_unit_id = mv_char.get('gameCharacterUnitId')
            mv_characters_by_music[music_id].append({
                'characterUnitId': char_unit_id,
                'defaultMusicType': mv_char.get('defaultMusicType', ''),
                'dancePriority': mv_char.get('dancePriority', 0)
            })

        difficulties_by_music = {}
        for diff in self.music_difficulties:
            music_id = diff['musicId']
            if music_id not in difficulties_by_music:
                difficulties_by_music[music_id] = []
            difficulties_by_music[music_id].append(diff)

        tags_by_music = {}
        for tag in self.music_tags:
            music_id = tag['musicId']
            if music_id not in tags_by_music:
                tags_by_music[music_id] = []
            tags_by_music[music_id].append(tag['musicTag'])

        # 构建原曲视频链接映射
        original_video_by_music = {}
        for original in self.music_originals:
            music_id = original['musicId']
            original_video_by_music[music_id] = original.get('videoLink', '')

        # 提取和整合数据
        result = []
        for music in self.musics:
            music_id = music['id']

            # 应用过滤器
            if filter_opts.get('music_ids') and music_id not in filter_opts['music_ids']:
                continue

            if filter_opts.get('tags'):
                music_tags = tags_by_music.get(music_id, [])
                if not any(tag in music_tags for tag in filter_opts['tags']):
                    continue

            # 整合数据
            integrated_music = {
                'id': music_id,
                'title': music.get('title', ''),
                'pronunciation': music.get('pronunciation', ''),
                'lyricist': music.get('lyricist', ''),
                'composer': music.get('composer', ''),
                'arranger': music.get('arranger', ''),
                'categories': music.get('categories', []),
                'publishedAt': self._format_timestamp(music.get('publishedAt')),
                'releasedAt': self._format_timestamp(music.get('releasedAt')),
                'isNewlyWrittenMusic': music.get('isNewlyWrittenMusic', False),
                'isFullLength': music.get('isFullLength', False),

                # 演唱版本（包含演唱者和MV信息）
                'vocals': vocals_by_music.get(music_id, []),

                # MV舞蹈角色信息
                'mvCharacters': mv_characters_by_music.get(music_id, []),

                # 难度信息
                'difficulties': difficulties_by_music.get(music_id, []),

                # 标签
                'tags': tags_by_music.get(music_id, []),

                # 原曲MV视频链接
                'originalVideoLink': original_video_by_music.get(music_id, None)
            }

            # 应用难度过滤
            if filter_opts.get('min_level'):
                max_level = max([d.get('playLevel', 0) for d in integrated_music['difficulties']], default=0)
                if max_level < filter_opts['min_level']:
                    continue

            result.append(integrated_music)

            # 应用数量限制
            if filter_opts.get('limit') and len(result) >= filter_opts['limit']:
                break

        return result

    def _format_timestamp(self, timestamp_ms: int) -> str:
        """将时间戳转换为可读格式（日本时区 UTC+9）"""
        if not timestamp_ms:
            return None
        try:
            from datetime import timezone, timedelta
            # 使用日本标准时间 (JST = UTC+9)
            jst = timezone(timedelta(hours=9))
            dt = datetime.fromtimestamp(timestamp_ms / 1000, tz=jst)
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            return None

    def export_to_json(self, data: List[Dict], output_file: str):
        """导出为JSON格式"""
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ 已导出到: {output_file}")

    def export_to_csv(self, data: List[Dict], output_file: str):
        """导出为CSV格式（简化版，不包含嵌套数据）"""
        import csv

        if not data:
            print("⚠️  没有数据可导出")
            return

        with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
            # 提取基础字段
            fieldnames = ['id', 'title', 'pronunciation', 'lyricist', 'composer',
                         'arranger', 'publishedAt', 'releasedAt', 'tags_count',
                         'vocals_count', 'max_difficulty_level']

            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()

            for music in data:
                row = {
                    'id': music['id'],
                    'title': music['title'],
                    'pronunciation': music['pronunciation'],
                    'lyricist': music['lyricist'],
                    'composer': music['composer'],
                    'arranger': music['arranger'],
                    'publishedAt': music['publishedAt'],
                    'releasedAt': music['releasedAt'],
                    'tags_count': len(music.get('tags', [])),
                    'vocals_count': len(music.get('vocals', [])),
                    'max_difficulty_level': max([d.get('playLevel', 0) for d in music.get('difficulties', [])], default=0)
                }
                writer.writerow(row)

        print(f"✅ 已导出到: {output_file}")

    def export_to_sql(self, data: List[Dict], output_file: str, table_prefix: str = 'sekai'):
        """导出为SQL INSERT语句"""
        with open(output_file, 'w', encoding='utf-8') as f:
            # 创建表结构
            f.write(f"""-- Project Sekai 音乐数据库
-- 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

-- 音乐主表
CREATE TABLE IF NOT EXISTS {table_prefix}_musics (
    id INT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    pronunciation VARCHAR(255),
    lyricist VARCHAR(255),
    composer VARCHAR(255),
    arranger VARCHAR(255),
    published_at DATETIME,
    released_at DATETIME,
    is_newly_written BOOLEAN,
    is_full_length BOOLEAN,
    original_video_link TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 音乐标签表
CREATE TABLE IF NOT EXISTS {table_prefix}_music_tags (
    id INT AUTO_INCREMENT PRIMARY KEY,
    music_id INT NOT NULL,
    tag VARCHAR(100) NOT NULL,
    FOREIGN KEY (music_id) REFERENCES {table_prefix}_musics(id)
);

-- 音乐难度表
CREATE TABLE IF NOT EXISTS {table_prefix}_music_difficulties (
    id INT PRIMARY KEY,
    music_id INT NOT NULL,
    difficulty ENUM('easy', 'normal', 'hard', 'expert', 'master', 'append'),
    play_level INT,
    total_note_count INT,
    FOREIGN KEY (music_id) REFERENCES {table_prefix}_musics(id)
);

-- 音乐演唱版本表
CREATE TABLE IF NOT EXISTS {table_prefix}_music_vocals (
    id INT PRIMARY KEY,
    music_id INT NOT NULL,
    vocal_type VARCHAR(50),
    caption VARCHAR(255),
    seq INT,
    FOREIGN KEY (music_id) REFERENCES {table_prefix}_musics(id)
);

-- 演唱版本-歌手关联表
CREATE TABLE IF NOT EXISTS {table_prefix}_vocal_singers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    vocal_id INT NOT NULL,
    character_id INT NOT NULL,
    character_name VARCHAR(100),
    character_type VARCHAR(50),
    unit_name VARCHAR(100),
    FOREIGN KEY (vocal_id) REFERENCES {table_prefix}_music_vocals(id)
);

-- MV资源变体表
CREATE TABLE IF NOT EXISTS {table_prefix}_mv_variants (
    id INT PRIMARY KEY,
    vocal_id INT NOT NULL,
    asset_bundle_name VARCHAR(255),
    FOREIGN KEY (vocal_id) REFERENCES {table_prefix}_music_vocals(id)
);

""")

            # 插入音乐数据
            f.write(f"\n-- 插入音乐数据\n")
            for music in data:
                f.write(f"INSERT INTO {table_prefix}_musics (id, title, pronunciation, lyricist, composer, arranger, published_at, released_at, is_newly_written, is_full_length, original_video_link) VALUES\n")
                f.write(f"  ({music['id']}, ")
                f.write(f"{self._sql_escape(music['title'])}, ")
                f.write(f"{self._sql_escape(music.get('pronunciation'))}, ")
                f.write(f"{self._sql_escape(music.get('lyricist'))}, ")
                f.write(f"{self._sql_escape(music.get('composer'))}, ")
                f.write(f"{self._sql_escape(music.get('arranger'))}, ")
                f.write(f"{self._sql_escape(music.get('publishedAt'))}, ")
                f.write(f"{self._sql_escape(music.get('releasedAt'))}, ")
                f.write(f"{1 if music.get('isNewlyWrittenMusic') else 0}, ")
                f.write(f"{1 if music.get('isFullLength') else 0}, ")
                f.write(f"{self._sql_escape(music.get('originalVideoLink'))}")
                f.write(");\n")

                # 插入标签
                for tag in music.get('tags', []):
                    f.write(f"INSERT INTO {table_prefix}_music_tags (music_id, tag) VALUES ({music['id']}, {self._sql_escape(tag)});\n")

                # 插入难度
                for diff in music.get('difficulties', []):
                    f.write(f"INSERT INTO {table_prefix}_music_difficulties (id, music_id, difficulty, play_level, total_note_count) VALUES ")
                    f.write(f"({diff['id']}, {music['id']}, {self._sql_escape(diff.get('musicDifficulty'))}, {diff.get('playLevel', 0)}, {diff.get('totalNoteCount', 0)});\n")

                # 插入演唱版本
                for vocal in music.get('vocals', []):
                    vocal_id = vocal['id']
                    f.write(f"INSERT INTO {table_prefix}_music_vocals (id, music_id, vocal_type, caption, seq) VALUES ")
                    f.write(f"({vocal_id}, {music['id']}, {self._sql_escape(vocal.get('musicVocalType'))}, {self._sql_escape(vocal.get('caption'))}, {vocal.get('seq', 0)});\n")

                    # 插入演唱者
                    for singer in vocal.get('singers', []):
                        f.write(f"INSERT INTO {table_prefix}_vocal_singers (vocal_id, character_id, character_name, character_type, unit_name) VALUES ")
                        f.write(f"({vocal_id}, {singer['id']}, {self._sql_escape(singer['name'])}, {self._sql_escape(singer.get('characterType'))}, {self._sql_escape(singer.get('unit'))});\n")

                    # 插入MV变体
                    for mv_variant in vocal.get('mvVariants', []):
                        f.write(f"INSERT INTO {table_prefix}_mv_variants (id, vocal_id, asset_bundle_name) VALUES ")
                        f.write(f"({mv_variant['id']}, {vocal_id}, {self._sql_escape(mv_variant.get('assetbundleName'))});\n")

                f.write("\n")

        print(f"✅ 已导出到: {output_file}")

    def _sql_escape(self, value) -> str:
        """SQL字符串转义"""
        if value is None:
            return 'NULL'
        if isinstance(value, (int, float)):
            return str(value)
        # 转义单引号
        escaped_value = str(value).replace("'", "''")
        return f"'{escaped_value}'"


def main():
    """主函数 - 使用示例"""

    # 设置数据目录
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'sekai-master-db-diff-main')

    # 创建提取器
    extractor = MusicDataExtractor(data_dir)

    # 加载数据
    extractor.load_all_data()

    print("\n" + "="*60)
    print("请选择提取方式:")
    print("="*60)
    print("1. 提取所有音乐（完整数据）")
    print("2. 提取前50首音乐（用于测试）")
    print("3. 提取VOCALOID标签的音乐")
    print("4. 提取高难度音乐（Master 25+）")
    print("5. 自定义提取")
    print("="*60)

    choice = input("\n请输入选项 (1-5): ").strip()

    filter_opts = {}

    if choice == '1':
        filter_opts = {}
        output_name = 'all_musics'
    elif choice == '2':
        filter_opts = {'limit': 50}
        output_name = 'top_50_musics'
    elif choice == '3':
        filter_opts = {'tags': ['vocaloid']}
        output_name = 'vocaloid_musics'
    elif choice == '4':
        filter_opts = {'min_level': 25}
        output_name = 'hard_musics'
    elif choice == '5':
        print("\n自定义过滤选项:")
        limit = input("限制数量 (留空=不限制): ").strip()
        if limit:
            filter_opts['limit'] = int(limit)

        tags = input("标签过滤 (逗号分隔，如: vocaloid,light_music_club): ").strip()
        if tags:
            filter_opts['tags'] = [t.strip() for t in tags.split(',')]

        min_level = input("最低难度等级 (留空=不限制): ").strip()
        if min_level:
            filter_opts['min_level'] = int(min_level)

        output_name = 'custom_musics'
    else:
        print("❌ 无效选项")
        return

    # 提取数据
    print(f"\n🔍 开始提取数据...")
    music_data = extractor.extract_music_list(filter_opts)
    print(f"✅ 提取了 {len(music_data)} 首音乐")

    # 导出数据
    print("\n📤 选择导出格式:")
    print("1. JSON (推荐，包含完整数据)")
    print("2. CSV (简化版，适合Excel)")
    print("3. SQL (直接导入数据库)")
    print("4. 全部导出")

    export_choice = input("\n请输入选项 (1-4): ").strip()

    # 生成带时间戳的文件夹名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    folder_name = f'{timestamp}_{output_name}'

    # 创建独立的输出文件夹
    output_dir = os.path.join(data_dir, 'extracted', folder_name)
    os.makedirs(output_dir, exist_ok=True)

    # 文件名不需要再带时间戳，因为文件夹已经有了
    base_filename = output_name

    if export_choice in ['1', '4']:
        extractor.export_to_json(music_data, os.path.join(output_dir, f'{base_filename}.json'))

    if export_choice in ['2', '4']:
        extractor.export_to_csv(music_data, os.path.join(output_dir, f'{base_filename}.csv'))

    if export_choice in ['3', '4']:
        extractor.export_to_sql(music_data, os.path.join(output_dir, f'{base_filename}.sql'))

    print(f"\n🎉 提取完成！文件保存在: {output_dir}")

    # 显示示例数据
    if music_data:
        print("\n" + "="*60)
        print("📊 示例数据预览（第一首）:")
        print("="*60)
        first_music = music_data[0]
        print(f"ID: {first_music['id']}")
        print(f"标题: {first_music['title']}")
        print(f"作曲: {first_music['composer']}")
        print(f"标签: {', '.join(first_music['tags'])}")
        print(f"演唱版本数: {len(first_music['vocals'])}")
        print(f"难度数: {len(first_music['difficulties'])}")
        if first_music['difficulties']:
            levels = [d['playLevel'] for d in first_music['difficulties']]
            print(f"难度等级: {min(levels)} ~ {max(levels)}")
        if first_music.get('originalVideoLink'):
            print(f"原曲MV: {first_music['originalVideoLink']}")

        # 显示演唱版本详情
        if first_music['vocals']:
            print(f"\n演唱版本详情:")
            for vocal in first_music['vocals'][:3]:  # 只显示前3个版本
                print(f"  - {vocal.get('caption', 'N/A')}")
                if vocal.get('singers'):
                    singer_names = [s['name'] for s in vocal['singers']]
                    print(f"    演唱: {', '.join(singer_names)}")
                if vocal.get('mvVariants'):
                    print(f"    MV变体数: {len(vocal['mvVariants'])}")


if __name__ == '__main__':
    main()
