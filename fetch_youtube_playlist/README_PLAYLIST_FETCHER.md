# YouTube Playlist 视频信息抓取工具

## 📖 功能介绍

这个工具可以从 YouTube Playlist 中提取所有视频的详细信息，包括：

- ✅ 视频标题
- ✅ 视频链接（URL）
- ✅ 视频描述（完整简介）
- ✅ 缩略图（多种分辨率）
- ✅ 频道名称和ID
- ✅ 发布时间
- ✅ 视频位置（在 Playlist 中的顺序）

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

**最小依赖**（仅使用 yt-dlp 方案）：
```bash
pip install requests yt-dlp
```

**完整依赖**（支持 API 方案）：
```bash
pip install requests yt-dlp google-api-python-client
```

### 2️⃣ 运行脚本

**方式一：交互式运行**
```bash
python fetch_youtube_playlist.py
```
然后按提示输入 Playlist URL。

**方式二：修改代码运行**
编辑 `fetch_youtube_playlist.py` 的 `main()` 函数，直接设置 `PLAYLIST_URL`。

### 3️⃣ 使用 API Key（可选但推荐）

如果你有 YouTube API Key，可以通过以下方式设置：

**方法1：环境变量**
```bash
# Windows
set YOUTUBE_API_KEY=your_api_key_here

# Linux/Mac
export YOUTUBE_API_KEY=your_api_key_here
```

**方法2：直接修改代码**
编辑 `fetch_youtube_playlist.py` 第 346 行：
```python
API_KEY = 'your_api_key_here'
```

---

## 🔧 高级用法

### 作为 Python 模块使用

```python
from fetch_youtube_playlist import YouTubePlaylistFetcher

# 创建抓取器（可选提供 API Key）
fetcher = YouTubePlaylistFetcher(api_key='your_api_key_here')

# 抓取 Playlist
playlist_url = 'https://www.youtube.com/playlist?list=PLxxxxxxxxxxx'
videos = fetcher.fetch_playlist(playlist_url)

# 保存为 JSON
fetcher.save_to_json('output.json')

# 下载缩略图
fetcher.download_thumbnails(output_dir='thumbnails', quality='high')

# 打印摘要
fetcher.print_summary()
```

### 自定义配置

```python
# 只使用 yt-dlp（不使用 API）
videos = fetcher.fetch_playlist(playlist_url, use_api_first=False)

# 只使用 API
videos = fetcher.fetch_with_api(playlist_id='PLxxxxxxxxxxx', max_results=100)

# 下载不同质量的缩略图
# 可选: default, medium, high, standard, maxres
fetcher.download_thumbnails(quality='maxres')
```

---

## 📊 输出格式

### JSON 文件结构

```json
{
  "metadata": {
    "fetchedAt": "2026-01-22T12:00:00",
    "totalVideos": 150,
    "fetchMethod": "API"
  },
  "videos": [
    {
      "videoId": "xxxxxxxxxxx",
      "url": "https://www.youtube.com/watch?v=xxxxxxxxxxx",
      "title": "视频标题",
      "description": "完整的视频描述...",
      "channelTitle": "频道名称",
      "channelId": "UCxxxxxxxxxxxxxxxxx",
      "publishedAt": "2023-01-01T00:00:00Z",
      "thumbnails": {
        "default": "https://i.ytimg.com/vi/xxx/default.jpg",
        "medium": "https://i.ytimg.com/vi/xxx/mqdefault.jpg",
        "high": "https://i.ytimg.com/vi/xxx/hqdefault.jpg",
        "standard": "https://i.ytimg.com/vi/xxx/sddefault.jpg",
        "maxres": "https://i.ytimg.com/vi/xxx/maxresdefault.jpg"
      },
      "position": 0
    }
  ]
}
```

---

## 🔑 如何申请 YouTube API Key

### 步骤详解（5-10分钟）

1. **访问 Google Cloud Console**
   - 打开: https://console.cloud.google.com/

2. **创建新项目**
   - 点击顶部项目下拉菜单
   - 点击"新建项目"
   - 输入项目名称（如 "YouTube Playlist Fetcher"）
   - 点击"创建"

3. **启用 YouTube Data API v3**
   - 在左侧菜单选择"API和服务" → "库"
   - 搜索 "YouTube Data API v3"
   - 点击进入，点击"启用"

4. **创建 API 凭据**
   - 在左侧菜单选择"API和服务" → "凭据"
   - 点击"创建凭据" → 选择"API 密钥"
   - 复制生成的 API 密钥
   - （可选）点击"限制密钥"，选择"限制密钥" → "YouTube Data API v3"

5. **使用 API Key**
   - 将 API Key 设置为环境变量或写入代码

### API 配额说明

- **每日免费配额**: 10,000 units
- **获取 Playlist 视频列表**: 每次 1 unit
- **每次最多获取**: 50 个视频
- **预估可获取**: 每天约 500 个视频（含详细信息）

---

## ⚙️ 两种方案对比

| 特性 | YouTube Data API v3 | yt-dlp |
|------|---------------------|---------|
| **需要 API Key** | ✅ 是 | ❌ 否 |
| **配额限制** | ✅ 10,000 units/天 | ❌ 无限制 |
| **速度** | ⚡ 快 | 🐌 较慢 |
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **数据完整性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **被限流风险** | ❌ 低 | ⚠️ 中等 |
| **推荐场景** | 频繁抓取、大量数据 | 一次性抓取、小量数据 |

**建议**: 使用混合方案，优先 API，备用 yt-dlp

---

## 🎯 Project Sekai 使用建议

### 步骤1：找到官方 Playlist

访问 Project Sekai 官方 YouTube 频道，找到 2DMV Playlist，例如：
```
https://www.youtube.com/playlist?list=PLxxxxxxxxxxx
```

### 步骤2：运行抓取

```bash
python fetch_youtube_playlist.py
```

输入 Playlist URL，等待抓取完成。

### 步骤3：提取创作者信息

抓取完成后，从 `description` 字段提取 2DMV 创作者信息。

常见模式：
- `2DMV: 创作者名称`
- `映像: 创作者名称`
- `Movie: 创作者名称`
- `動画: 创作者名称`

可以使用正则表达式：
```python
import re

for video in videos:
    desc = video['description']

    # 匹配常见模式
    patterns = [
        r'2DMV[:\s]+(.+?)(?:\n|$)',
        r'映像[:\s]+(.+?)(?:\n|$)',
        r'Movie[:\s]+(.+?)(?:\n|$)',
        r'動画[:\s]+(.+?)(?:\n|$)',
    ]

    for pattern in patterns:
        match = re.search(pattern, desc, re.IGNORECASE)
        if match:
            creator = match.group(1).strip()
            print(f"{video['title']} - 创作者: {creator}")
            break
```

### 步骤4：关联到现有数据

将获取的信息与 `all_musics.json` 中的数据关联：

```python
import json

# 加载现有数据
with open('extracted/20260122_111229_all_musics/all_musics.json', 'r', encoding='utf-8') as f:
    all_musics = json.load(f)

# 加载 Playlist 数据
with open('playlist_videos_20260122_120000.json', 'r', encoding='utf-8') as f:
    playlist_data = json.load(f)

# 通过标题或 URL 关联
youtube_map = {video['url']: video for video in playlist_data['videos']}

for music in all_musics:
    original_link = music.get('originalVideoLink')
    if original_link in youtube_map:
        youtube_info = youtube_map[original_link]
        music['youtubeTitle'] = youtube_info['title']
        music['youtubeDescription'] = youtube_info['description']
        music['youtubeChannel'] = youtube_info['channelTitle']
        # ... 提取创作者信息

# 保存增强后的数据
with open('all_musics_enhanced.json', 'w', encoding='utf-8') as f:
    json.dump(all_musics, f, ensure_ascii=False, indent=2)
```

---

## ❓ 常见问题

### Q1: API 配额用完了怎么办？

**A**: 脚本会自动切换到 yt-dlp 方案继续抓取。或者：
- 等待第二天配额重置（太平洋时间午夜）
- 创建多个 Google Cloud 项目，使用多个 API Key

### Q2: yt-dlp 抓取失败？

**A**: 可能原因：
- 网络问题（尝试使用代理）
- Playlist 是私有的
- 视频被删除或限制

### Q3: 如何提高抓取速度？

**A**:
- 使用 API 方案（比 yt-dlp 快 10 倍以上）
- 不下载缩略图（或稍后批量下载）
- 减少延迟时间（但可能被限流）

### Q4: 可以抓取私有 Playlist 吗？

**A**:
- API 方案：不支持
- yt-dlp：需要提供 cookies 文件

---

## 📝 许可证

本工具仅供学习和个人使用，请遵守 YouTube 服务条款。

---

## 🙏 致谢

- YouTube Data API v3
- yt-dlp 项目
- Project Sekai 官方

---

**祝你抓取愉快！** 🎉
