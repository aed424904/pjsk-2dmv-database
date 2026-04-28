#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
文本规范化工具
"""

import re
import unicodedata


class TextNormalizer:
    """文本规范化器"""

    def __init__(self):
        """初始化"""
        pass

    def normalize(self, text: str) -> str:
        """规范化文本"""
        if not text:
            return ''

        # 1. Unicode规范化（NFKC）
        text = unicodedata.normalize('NFKC', text)

        # 2. 移除首尾空格
        text = text.strip()

        # 3. 移除括号内容（通常是补充说明）
        # 例如: "kz (livetune)" -> "kz"
        text = re.sub(r'\s*[（(][^）)]*[）)]', '', text)

        # 4. 移除多余的空格
        text = re.sub(r'\s+', ' ', text)

        # 5. 移除常见的前缀/后缀
        text = re.sub(r'^(?:Produced\s+by|Composed\s+by|Written\s+by)\s+', '', text, flags=re.IGNORECASE)

        # 6. 规范化常见的分隔符
        text = text.replace('、', ',').replace('，', ',')

        # 7. 处理多个创作者的情况
        # 例如: "AAA x BBB" -> "AAA, BBB"
        text = re.sub(r'\s+[x×]\s+', ', ', text)

        return text.strip()

    def split_multiple_creators(self, text: str) -> list:
        """分割多个创作者"""
        if not text:
            return []

        # 使用常见的分隔符分割
        creators = re.split(r'[,&＆、，]|\s+x\s+|\s+×\s+', text)

        # 清理和过滤
        creators = [c.strip() for c in creators if c.strip()]

        return creators
