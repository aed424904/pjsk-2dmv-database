#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
配置文件
"""

import os

# 基础路径
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 数据源配置
CONFIG = {
    # 数据源文件
    'source_file': os.path.join(BASE_DIR, '..', 'sekai-master-db-diff-main', 'musicOriginals.json'),

    # 输出目录
    'output_dir': os.path.join(BASE_DIR, 'output'),
    'cache_dir': os.path.join(BASE_DIR, 'output', 'cache'),
    'log_dir': os.path.join(BASE_DIR, 'logs'),

    # yt-dlp 配置选项
    'ytdlp_opts': {
        'quiet': True,                    # 静默模式
        'no_warnings': True,              # 不显示警告
        'extract_flat': False,            # 提取完整信息
        'skip_download': True,            # 不下载视频文件
        'socket_timeout': 30,             # 超时 30 秒
        'ignoreerrors': True,             # 忽略错误继续
        'no_check_certificate': True,     # 跳过证书检查
    },

    # 性能配置
    'batch_size': 20,                     # 每批处理的视频数量
    'max_workers': 5,                     # 最大并发线程数
    'delay_between_requests': 1.5,        # 请求间隔（秒）
    'cache_expiry_days': 7,               # 缓存有效期（天）

    # 重试配置
    'retry': {
        'max_attempts': 3,                # 最大重试次数
        'base_delay': 1.0,                # 基础延迟（秒）
        'exponential_base': 2.0,          # 指数退避基数
        'max_delay': 60.0,                # 最大延迟（秒）
        'rate_limit_wait': 60.0,          # 限流等待时间（秒）
    },

    # 速率限制
    'rate_limits': {
        'youtube': {
            'requests_per_minute': 30,
            'delay_between_requests': 2.0,
        },
        'niconico': {
            'requests_per_minute': 10,
            'delay_between_requests': 6.0,
        },
    },

    # 代理设置（可选）
    'proxy': None,  # 例如: 'http://127.0.0.1:7890'
}

# 错误类型定义
ERROR_TYPES = {
    'VIDEO_UNAVAILABLE': '视频不可用（已删除/私密）',
    'GEO_RESTRICTED': '地区限制',
    'NETWORK_ERROR': '网络错误',
    'RATE_LIMITED': '请求过于频繁',
    'PARSE_ERROR': '解析失败',
    'UNKNOWN': '未知错误',
}

# 可重试的错误类型
RETRYABLE_ERRORS = ['GEO_RESTRICTED', 'NETWORK_ERROR', 'RATE_LIMITED', 'PARSE_ERROR', 'UNKNOWN']
