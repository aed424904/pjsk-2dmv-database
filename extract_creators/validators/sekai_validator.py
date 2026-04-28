#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Sekai Viewer数据验证器
"""

import json
import unicodedata
from typing import Dict, Optional


class SekaiValidator:
    """Sekai Viewer数据验证器"""

    def __init__(self, sekai_music_file: str):
        """初始化"""
        with open(sekai_music_file, 'r', encoding='utf-8') as f:
            self.sekai_musics = json.load(f)

        # 构建索引
        self.music_by_id = {m['id']: m for m in self.sekai_musics}

    def get_music_creators(self, music_id: int) -> Dict[str, Optional[str]]:
        """获取Sekai Viewer中的创作者信息"""
        music = self.music_by_id.get(music_id)
        if not music:
            return {}

        return {
            'lyricist': music.get('lyricist', ''),
            'composer': music.get('composer', ''),
            'arranger': music.get('arranger', ''),
        }

    def validate(self, extracted: Dict, sekai_data: Dict) -> Dict:
        """验证提取结果与Sekai数据的一致性"""
        conflicts = []
        is_valid = True
        needs_review = False

        for field in ['lyricist', 'composer', 'arranger']:
            extracted_value = extracted.get(field, '')
            sekai_value = sekai_data.get(field, '')

            if not extracted_value and not sekai_value:
                continue

            if not extracted_value and sekai_value:
                # 提取失败，但Sekai有数据
                conflicts.append({
                    'field': field,
                    'issue': 'missing_extraction',
                    'extracted': None,
                    'sekai': sekai_value,
                })
                needs_review = True
                is_valid = False

            elif extracted_value and not sekai_value:
                # 提取到了，但Sekai没有数据（可能是补充）
                conflicts.append({
                    'field': field,
                    'issue': 'extra_extraction',
                    'extracted': extracted_value,
                    'sekai': None,
                })
                needs_review = True

            elif extracted_value != sekai_value:
                # 数据不一致
                # 使用模糊匹配判断是否实质相同
                if not self._fuzzy_match(extracted_value, sekai_value):
                    conflicts.append({
                        'field': field,
                        'issue': 'mismatch',
                        'extracted': extracted_value,
                        'sekai': sekai_value,
                    })
                    needs_review = True
                    is_valid = False

        return {
            'isValid': is_valid,
            'needsReview': needs_review,
            'conflicts': conflicts,
        }

    def _fuzzy_match(self, text1: str, text2: str) -> bool:
        """模糊匹配（处理空格、大小写、全半角等差异）"""
        if not text1 or not text2:
            return False

        def normalize(s):
            s = unicodedata.normalize('NFKC', s)
            s = s.lower()
            s = s.replace(' ', '').replace('　', '')
            return s

        return normalize(text1) == normalize(text2)
