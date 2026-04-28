# 原曲视频信息抓取工具

使用 yt-dlp 从 `musicOriginals.json` 抓取 YouTube 和 Niconico 视频的详细元数据。

## ✨ 特性

- ✅ **双平台支持**: YouTube + Niconico
- ✅ **无需 API 密钥**: 使用 yt-dlp，不受 YouTube API 配额限制
- ✅ **智能缓存**: 避免重复抓取，缓存有效期 7 天
- ✅ **错误处理**: 自动重试，指数退避策略
- ✅ **断点续传**: 支持中断后继续
- ✅ **进度跟踪**: 实时显示进度条和统计信息
- ✅ **代理支持**: 可配置代理服务器

## 📦 安装

### 1. 安装 Python 依赖

```bash
cd fetch_original_videos
pip install -r requirements.txt
```

### 2. 验证 yt-dlp 安装

```bash
yt-dlp --version
```

## 🚀 使用方法

### 基础命令

```bash
# 全量抓取（推荐）
python fetch_original_videos.py

# 限制数量测试（抓取前 10 个）
python fetch_original_videos.py --limit 10

# 从断点继续
python fetch_original_videos.py --resume

# 重试失败的视频
python fetch_original_videos.py --retry-failed

# 不使用缓存（强制重新抓取）
python fetch_original_videos.py --no-cache

# 使用代理（针对地区限制）
python fetch_original_videos.py --proxy http://127.0.0.1:7890
```

### 命令行参数

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--source` | 数据源文件路径 | `../sekai-master-db-diff-main/musicOriginals.json` |
| `--output-dir` | 输出目录 | `output/` |
| `--batch-size` | 每批处理的视频数量 | `20` |
| `--resume` | 从上次中断处继续 | - |
| `--retry-failed` | 重试之前失败的视频 | - |
| `--no-cache` | 不使用缓存 | - |
| `--proxy` | 代理服务器地址 | - |
| `--limit` | 限制处理的视频数量（测试用） | - |

## 📊 输出文件

### 1. 成功结果：`output/video_info_{timestamp}.json`

```json
{
  "metadata": {
    "fetchedAt": "2026-01-29T10:00:00Z",
    "source": "../sekai-master-db-diff-main/musicOriginals.json",
    "totalVideos": 254,
    "successCount": 240,
    "failedCount": 14,
    "cachedCount": 50,
    "platformDistribution": {
      "youtube": {
        "total": 230,
        "success": 228,
        "failed": 2
      },
      "niconico": {
        "total": 24,
        "success": 12,
        "failed": 12
      }
    }
  },
  "videos": [
    {
      "id": 1,
      "musicId": 1,
      "videoLink": "https://youtu.be/PqJNc9KVIZE",
      "platform": "youtube",
      "videoId": "PqJNc9KVIZE",
      "metadata": {
        "title": "Tell Your World",
        "description": "...",
        "uploader": "kz livetune",
        "uploaderId": "UC...",
        "uploadDate": "20120118",
        "duration": 270,
        "viewCount": 15000000,
        "likeCount": 250000,
        "commentCount": 12000,
        "thumbnailUrl": "https://...",
        "tags": ["VOCALOID", "初音ミク"]
      },
      "fetchedAt": "2026-01-29T10:00:00Z",
      "status": "success"
    }
  ]
}
```

### 2. 失败记录：`output/failed_videos.json`

```json
{
  "metadata": {
    "lastUpdated": "2026-01-29T10:30:00Z",
    "totalFailed": 14
  },
  "failed": [
    {
      "id": 13,
      "musicId": 13,
      "videoLink": "https://www.nicovideo.jp/watch/sm9874560",
      "platform": "niconico",
      "videoId": "sm9874560",
      "error": "Video unavailable",
      "errorType": "VIDEO_UNAVAILABLE",
      "errorDescription": "视频不可用（已删除/私密）",
      "attempts": 3,
      "lastAttempt": "2026-01-29T10:15:00Z"
    }
  ]
}
```

### 3. 缓存文件：`output/cache/{platform}/{videoId}.json`

缓存按平台分类存储，有效期 7 天。

### 4. 进度文件：`output/progress.json`

用于断点续传，记录已处理的视频 ID。

## ⚙️ 配置

可以在 `config.py` 中修改配置：

```python
CONFIG = {
    # 批量处理配置
    'batch_size': 20,                     # 每批处理的视频数量
    'max_workers': 5,                     # 最大并发线程数
    'delay_between_requests': 1.5,        # 请求间隔（秒）

    # 缓存配置
    'cache_expiry_days': 7,               # 缓存有效期（天）

    # 重试配置
    'retry': {
        'max_attempts': 3,                # 最大重试次数
        'base_delay': 1.0,                # 基础延迟（秒）
        'exponential_base': 2.0,          # 指数退避基数
    },

    # yt-dlp 配置
    'ytdlp_opts': {
        'socket_timeout': 30,             # 超时时间
        # ...更多选项
    },
}
```

## 🔧 故障排除

### 问题 1: yt-dlp 安装失败

```bash
# 使用 pip 安装
pip install yt-dlp

# 或使用国内镜像
pip install yt-dlp -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 问题 2: Niconico 视频抓取失败率高

Niconico 的视频可能需要登录或存在地区限制。可以：
- 使用代理服务器
- 手动补充缺失的数据

### 问题 3: 抓取速度慢

- 减少 `delay_between_requests`（可能导致限流）
- 增加 `batch_size`
- 使用更快的网络连接

### 问题 4: 缓存占用空间大

定期清理过期缓存：

```bash
# 在 Python 中运行
from utils.cache_manager import CacheManager
cache_mgr = CacheManager('output/cache')
cleared = cache_mgr.clear_expired()
print(f"已清理 {cleared} 个过期缓存")
```

## 📝 常见问题

**Q: 为什么不使用 YouTube Data API？**
A: yt-dlp 无需 API 密钥，不受配额限制，更适合批量抓取。

**Q: 抓取需要多长时间？**
A: 约 10-15 分钟（254 个视频，控制速率避免限流）。

**Q: 可以并发抓取吗？**
A: 内部已实现线程池并发，但控制了速率避免被限流。

**Q: 缓存会自动更新吗？**
A: 缓存有效期 7 天，过期后会自动重新抓取。可使用 `--no-cache` 强制刷新。

## 📂 项目结构

```
fetch_original_videos/
├── fetch_original_videos.py          # 主脚本
├── config.py                         # 配置文件
├── requirements.txt                   # Python 依赖
├── README_ORIGINAL_VIDEOS.md         # 本文档
├── utils/
│   ├── __init__.py
│   ├── url_parser.py                 # URL 解析
│   ├── cache_manager.py              # 缓存管理
│   ├── error_handler.py              # 错误处理
│   └── video_fetcher.py              # yt-dlp 封装
├── output/
│   ├── video_info_{timestamp}.json   # 抓取结果
│   ├── failed_videos.json            # 失败记录
│   ├── progress.json                 # 进度记录
│   └── cache/                        # 缓存目录
│       ├── youtube/
│       └── niconico/
└── logs/
    └── fetch_{timestamp}.log         # 日志文件
```

## 🎯 最佳实践

1. **首次运行**: 使用 `--limit 10` 测试少量视频
2. **正式抓取**: 运行全量抓取，启用缓存
3. **处理失败**: 使用 `--retry-failed` 重试失败的视频
4. **定期更新**: 使用 `--no-cache` 刷新动态数据（观看数、点赞数）

## 📞 支持

如有问题，请检查：
1. Python 版本 >= 3.7
2. yt-dlp 已正确安装
3. 网络连接正常
4. 数据源文件路径正确

## 📄 许可

本工具遵循项目主许可协议。
