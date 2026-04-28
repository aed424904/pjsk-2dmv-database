#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
正则表达式模式匹配器
"""

import re
from typing import Optional


class PatternMatcher:
    """正则表达式模式匹配器"""

    def __init__(self):
        """初始化模式"""
        # 日文模式
        self.lyricist_patterns = [
            r'作詞[：:\s]*([^\n\r/・&,（(]+)',
            r'詞[：:\s]*([^\n\r/・&,（(]+)',
            r'Lyrics[：:\s]*([^\n\r/・&,（(]+)',
            r'Words[：:\s]*([^\n\r/・&,（(]+)',
        ]

        self.composer_patterns = [
            r'作曲[：:\s]*([^\n\r/・&,（(]+)',
            r'曲[：:\s]*([^\n\r/・&,（(]+)',
            r'Music[：:\s]*([^\n\r/・&,（(]+)',
            r'Compose[rd]?[：:\s]*([^\n\r/・&,（(]+)',
        ]

        self.arranger_patterns = [
            r'編曲[：:\s]*([^\n\r/・&,（(]+)',
            r'Arrange(?:ment)?[：:\s]*([^\n\r/・&,（(]+)',
        ]

        self.illustrator_patterns = [
            r'イラスト[：:\s]*([^\n\r/（(]+)',
            r'Illustration[：:\s]*([^\n\r/（(]+)',
            r'Illust[：:\s]*([^\n\r/（(]+)',
            r'絵[：:\s]*([^\n\r/（(]+)',
        ]

        self.video_director_patterns = [
            r'動画[：:\s]*([^\n\r/（(]+)',
            r'映像[：:\s]*([^\n\r/（(]+)',
            r'Video[：:\s]*([^\n\r/（(]+)',
            r'Music\s*Video\s*Director[：:\s]*([^\n\r/（(]+)',
        ]

        # 组合模式
        self.all_in_one_patterns = [
            r'作詞[・･&＆]作曲[・･&＆]編曲[：:\s]*([^\n\r/（(]+)',
            r'詞[・･/]曲[・･/]編[：:\s]*([^\n\r/（(]+)',
        ]

        self.lyricist_composer_patterns = [
            r'作詞[・･&＆]作曲[：:\s]*([^\n\r/（(]+)',
            r'Music\s*[&＆]\s*Words[：:\s]*([^\n\r/（(]+)',
            r'Words\s*[&＆]\s*Music[：:\s]*([^\n\r/（(]+)',
            r'詞[・･/]曲[：:\s]*([^\n\r/（(]+)',
        ]

    def _match_first(self, text: str, patterns: list) -> Optional[str]:
        """使用多个模式匹配，返回第一个匹配结果"""
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                result = match.group(1).strip()
                # 清理结果
                result = re.sub(r'\s*[（(].*?[）)]', '', result)  # 移除括号内容
                result = re.sub(r'\s+', ' ', result)  # 规范化空格
                return result
        return None

    def match_all_in_one(self, text: str) -> Optional[str]:
        """匹配全能型（作词・作曲・编曲）"""
        return self._match_first(text, self.all_in_one_patterns)

    def match_lyricist_composer(self, text: str) -> Optional[str]:
        """匹配作词作曲组合"""
        return self._match_first(text, self.lyricist_composer_patterns)

    def match_lyricist(self, text: str) -> Optional[str]:
        """匹配作词者"""
        return self._match_first(text, self.lyricist_patterns)

    def match_composer(self, text: str) -> Optional[str]:
        """匹配作曲者"""
        return self._match_first(text, self.composer_patterns)

    def match_arranger(self, text: str) -> Optional[str]:
        """匹配编曲者"""
        return self._match_first(text, self.arranger_patterns)

    def match_illustrator(self, text: str) -> Optional[str]:
        """匹配插画师"""
        return self._match_first(text, self.illustrator_patterns)

    def match_video_director(self, text: str) -> Optional[str]:
        """匹配视频制作"""
        return self._match_first(text, self.video_director_patterns)
