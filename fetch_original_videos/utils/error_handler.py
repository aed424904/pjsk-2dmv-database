#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
错误处理模块
负责处理各种错误情况并实现重试机制
"""

import time
from typing import Optional, Dict, Callable, Any
from datetime import datetime


class RetryConfig:
    """重试配置"""

    def __init__(
        self,
        max_attempts: int = 3,
        base_delay: float = 1.0,
        exponential_base: float = 2.0,
        max_delay: float = 60.0,
        rate_limit_wait: float = 60.0
    ):
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.exponential_base = exponential_base
        self.max_delay = max_delay
        self.rate_limit_wait = rate_limit_wait


class ErrorHandler:
    """错误处理器"""

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
    RETRYABLE_ERRORS = {'GEO_RESTRICTED', 'NETWORK_ERROR', 'RATE_LIMITED', 'PARSE_ERROR', 'UNKNOWN'}

    def __init__(self, config: Optional[RetryConfig] = None):
        """
        初始化错误处理器

        Args:
            config: 重试配置，如果为 None 则使用默认配置
        """
        self.config = config or RetryConfig()

    def classify_error(self, error: Exception) -> str:
        """
        分类错误类型

        Args:
            error: 异常对象

        Returns:
            错误类型代码
        """
        error_msg = str(error).lower()

        # 视频不可用
        if any(keyword in error_msg for keyword in ['unavailable', 'deleted', 'private', 'removed']):
            return 'VIDEO_UNAVAILABLE'

        # 地区限制
        if any(keyword in error_msg for keyword in ['geo', 'region', 'country', 'not available in your']):
            return 'GEO_RESTRICTED'

        # 网络错误
        if any(keyword in error_msg for keyword in ['network', 'connection', 'timeout', 'timed out']):
            return 'NETWORK_ERROR'

        # 限流
        if any(keyword in error_msg for keyword in ['rate limit', 'too many requests', '429']):
            return 'RATE_LIMITED'

        # 解析错误
        if any(keyword in error_msg for keyword in ['parse', 'extract', 'decode']):
            return 'PARSE_ERROR'

        # 未知错误
        return 'UNKNOWN'

    def is_retryable(self, error_type: str) -> bool:
        """
        判断错误是否可重试

        Args:
            error_type: 错误类型代码

        Returns:
            是否可重试
        """
        return error_type in self.RETRYABLE_ERRORS

    def get_retry_delay(self, attempt: int, error_type: str) -> float:
        """
        计算重试延迟时间（指数退避）

        Args:
            attempt: 当前尝试次数（从 1 开始）
            error_type: 错误类型

        Returns:
            延迟时间（秒）
        """
        # 如果是限流错误，使用固定的等待时间
        if error_type == 'RATE_LIMITED':
            return self.config.rate_limit_wait

        # 指数退避：base_delay * (exponential_base ^ (attempt - 1))
        delay = self.config.base_delay * (self.config.exponential_base ** (attempt - 1))

        # 不超过最大延迟
        return min(delay, self.config.max_delay)

    def retry_on_error(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        带重试机制地执行函数

        Args:
            func: 要执行的函数
            *args: 函数参数
            **kwargs: 函数关键字参数

        Returns:
            {
                'success': bool,
                'data': Any,          # 成功时的返回数据
                'error': str,         # 失败时的错误信息
                'error_type': str,    # 错误类型
                'attempts': int,      # 尝试次数
            }
        """
        last_error = None
        last_error_type = None

        for attempt in range(1, self.config.max_attempts + 1):
            try:
                # 执行函数
                result = func(*args, **kwargs)
                return {
                    'success': True,
                    'data': result,
                    'error': None,
                    'error_type': None,
                    'attempts': attempt,
                }

            except Exception as e:
                last_error = str(e)
                last_error_type = self.classify_error(e)

                # 如果不可重试，直接返回失败
                if not self.is_retryable(last_error_type):
                    break

                # 如果还有重试机会
                if attempt < self.config.max_attempts:
                    delay = self.get_retry_delay(attempt, last_error_type)
                    # print(f"⚠️  错误: {last_error_type}, 将在 {delay:.1f} 秒后重试 ({attempt}/{self.config.max_attempts})")
                    time.sleep(delay)
                    continue

                # 已达最大重试次数
                break

        # 所有尝试都失败
        return {
            'success': False,
            'data': None,
            'error': last_error,
            'error_type': last_error_type,
            'attempts': self.config.max_attempts,
        }

    def create_failure_record(
        self,
        video_info: Dict,
        error: str,
        error_type: str,
        attempts: int
    ) -> Dict:
        """
        创建失败记录

        Args:
            video_info: 视频基本信息
            error: 错误信息
            error_type: 错误类型
            attempts: 尝试次数

        Returns:
            失败记录数据
        """
        return {
            'id': video_info.get('id'),
            'musicId': video_info.get('musicId'),
            'videoLink': video_info.get('videoLink'),
            'platform': video_info.get('platform'),
            'videoId': video_info.get('videoId'),
            'error': error,
            'errorType': error_type,
            'errorDescription': self.ERROR_TYPES.get(error_type, '未知错误'),
            'attempts': attempts,
            'lastAttempt': datetime.now().isoformat(),
        }


# 测试代码
if __name__ == '__main__':
    handler = ErrorHandler()

    # 测试错误分类
    test_errors = [
        Exception("Video unavailable"),
        Exception("This video is not available in your country"),
        Exception("Connection timeout"),
        Exception("HTTP Error 429: Too Many Requests"),
    ]

    for err in test_errors:
        error_type = handler.classify_error(err)
        is_retryable = handler.is_retryable(error_type)
        print(f"错误: {err}")
        print(f"  类型: {error_type}")
        print(f"  可重试: {is_retryable}\n")
