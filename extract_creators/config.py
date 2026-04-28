#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CONFIG = {
    # 输入文件
    'video_info_file': os.path.join(BASE_DIR, '..', 'fetch_original_videos', 'output', 'video_info_20260129_171448.json'),
    'sekai_music_file': os.path.join(BASE_DIR, '..', 'sekai viewer_json', 'musics.json'),

    # 手动修正文件（可选）
    'manual_corrections_file': os.path.join(BASE_DIR, 'manual_corrections.json'),

    # 输出目录
    'output_dir': os.path.join(BASE_DIR, 'output'),
}
