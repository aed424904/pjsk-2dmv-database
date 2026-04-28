# YouTube Playlist 数据抓取完整方案

## 📑 目录

1. [方案概述](#方案概述)
2. [技术方案对比](#技术方案对比)
3. [方案一：YouTube Data API v3](#方案一youtube-data-api-v3)
4. [方案二：yt-dlp 工具](#方案二yt-dlp-工具)
5. [方案三：混合方案（推荐）](#方案三混合方案推荐)
6. [API Key 申请详细教程](#api-key-申请详细教程)
7. [私有 Playlist 抓取方案](#私有-playlist-抓取方案)
8. [完整代码实现](#完整代码实现)
9. [使用示例](#使用示例)
10. [故障排除](#故障排除)
11. [最佳实践](#最佳实践)

---

## 方案概述

### 目标

从 YouTube Playlist 中批量提取以下信息：

- ✅ **视频标题**（Title）
- ✅ **视频链接**（URL）
- ✅ **视频描述/简介**（Description）- 用于提取创作者信息
- ✅ **缩略图**（Thumbnails）- 多种分辨率
- ✅ **频道信息**（Channel Name & ID）
- ✅ **发布时间**（Published At）
- ✅ **视频位置**（Position in Playlist）
- ✅ **观看数/点赞数**（可选）

### 应用场景

- **Project Sekai 2DMV 数据库**：收集官方 Playlist 中所有 2DMV 视频信息
- **创作者信息提取**：从视频描述中提取动画制作者、插画师等信息
- **数据分析**：统计视频发布趋势、频道分布等

---

## 技术方案对比

### 方案对比表

| 特性 | YouTube Data API v3 | yt-dlp | 混合方案 |
|------|---------------------|--------|---------|
| **是否需要 API Key** | ✅ 是 | ❌ 否 | 🔄 可选 |
| **配额限制** | ✅ 10,000 units/天 | ❌ 无限制 | 🔄 智能切换 |
| **抓取速度** | ⚡ 很快（秒级） | 🐌 较慢（分钟级） | ⚡ 优先快速 |
| **稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **被限流风险** | ❌ 极低 | ⚠️ 中等 | ❌ 低 |
| **数据完整性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **支持私有 Playlist** | ❌ 否 | ✅ 是（需 cookies） | 🔄 部分支持 |
| **维护成本** | ❌ 低 | ⚠️ 中（需更新） | ❌ 低 |
| **推荐场景** | 频繁抓取、大量数据 | 一次性抓取、私有列表 | 所有场景 |

### 配额计算（API 方案）

**YouTube Data API v3 配额消耗：**

| 操作 | 消耗配额 | 说明 |
|------|---------|------|
| playlistItems.list | 1 unit | 获取 Playlist 视频列表（每次最多 50 个） |
| videos.list | 1 unit | 获取视频详细信息（每次最多 50 个） |

**示例计算：**

抓取一个包含 240 个视频的 Playlist：
- playlistItems.list: 240 ÷ 50 = 5 次请求 = **5 units**
- videos.list（可选）: 240 ÷ 50 = 5 次请求 = **5 units**
- **总计：5-10 units**

**结论：** 每天 10,000 units 配额可抓取约 **1,000-2,000 个视频**

---

## 方案一：YouTube Data API v3

### 1.1 方案原理

利用 Google 官方提供的 RESTful API 获取 YouTube 数据。

**工作流程：**

```
1. 提取 Playlist ID (从 URL)
   ↓
2. 调用 playlistItems.list API
   ↓
3. 获取视频列表（分页处理）
   ↓
4. 解析响应数据
   ↓
5. （可选）调用 videos.list 获取详细统计
```

### 1.2 具体实现代码

```python
import requests
import json
import time
from urllib.parse import urlparse, parse_qs

class YouTubeAPIFetcher:
    """YouTube Data API v3 抓取器"""

    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"

    def extract_playlist_id(self, url):
        """从 URL 提取 Playlist ID"""
        parsed = urlparse(url)
        if 'list' in parse_qs(parsed.query):
            return parse_qs(parsed.query)['list'][0]
        return None

    def fetch_playlist(self, playlist_id, max_results=500):
        """
        获取 Playlist 所有视频

        Args:
            playlist_id: Playlist ID
            max_results: 最大结果数（默认 500）

        Returns:
            list: 视频信息列表
        """
        videos = []
        next_page_token = None
        page_count = 0

        while True:
            page_count += 1
            print(f"正在获取第 {page_count} 页...")

            # 构建请求参数
            params = {
                'part': 'snippet,contentDetails',
                'playlistId': playlist_id,
                'maxResults': min(50, max_results - len(videos)),
                'key': self.api_key
            }

            if next_page_token:
                params['pageToken'] = next_page_token

            # 发送 API 请求
            url = f"{self.base_url}/playlistItems"
            response = requests.get(url, params=params)

            # 错误处理
            if response.status_code != 200:
                print(f"API 错误: {response.status_code}")
                print(f"错误信息: {response.text}")
                break

            data = response.json()

            # 解析视频信息
            for item in data.get('items', []):
                snippet = item['snippet']
                video_id = snippet['resourceId']['videoId']

                video_info = {
                    'videoId': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'title': snippet.get('title', ''),
                    'description': snippet.get('description', ''),
                    'channelTitle': snippet.get('channelTitle', ''),
                    'channelId': snippet.get('channelId', ''),
                    'publishedAt': snippet.get('publishedAt', ''),
                    'thumbnails': {
                        'default': snippet.get('thumbnails', {}).get('default', {}).get('url', ''),
                        'medium': snippet.get('thumbnails', {}).get('medium', {}).get('url', ''),
                        'high': snippet.get('thumbnails', {}).get('high', {}).get('url', ''),
                        'standard': snippet.get('thumbnails', {}).get('standard', {}).get('url', ''),
                        'maxres': snippet.get('thumbnails', {}).get('maxres', {}).get('url', '')
                    },
                    'position': snippet.get('position', 0)
                }
                videos.append(video_info)

            print(f"已获取 {len(videos)} 个视频")

            # 检查是否还有下一页
            next_page_token = data.get('nextPageToken')
            if not next_page_token or len(videos) >= max_results:
                break

            # 避免请求过快
            time.sleep(0.5)

        return videos

    def get_video_statistics(self, video_ids):
        """
        获取视频统计信息（观看数、点赞数等）

        Args:
            video_ids: 视频 ID 列表（最多 50 个）

        Returns:
            dict: 视频统计信息字典
        """
        if len(video_ids) > 50:
            print("警告: video_ids 超过 50 个，将只处理前 50 个")
            video_ids = video_ids[:50]

        params = {
            'part': 'statistics',
            'id': ','.join(video_ids),
            'key': self.api_key
        }

        url = f"{self.base_url}/videos"
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"获取统计信息失败: {response.status_code}")
            return {}

        data = response.json()
        stats = {}

        for item in data.get('items', []):
            video_id = item['id']
            statistics = item.get('statistics', {})
            stats[video_id] = {
                'viewCount': int(statistics.get('viewCount', 0)),
                'likeCount': int(statistics.get('likeCount', 0)),
                'commentCount': int(statistics.get('commentCount', 0))
            }

        return stats

# 使用示例
if __name__ == '__main__':
    API_KEY = 'your_api_key_here'
    PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLxxxxxxxxxxx'

    fetcher = YouTubeAPIFetcher(API_KEY)
    playlist_id = fetcher.extract_playlist_id(PLAYLIST_URL)

    if playlist_id:
        videos = fetcher.fetch_playlist(playlist_id)

        # 保存结果
        with open('playlist_api_result.json', 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'totalVideos': len(videos),
                    'method': 'API'
                },
                'videos': videos
            }, f, ensure_ascii=False, indent=2)

        print(f"\n成功抓取 {len(videos)} 个视频！")
```

### 1.3 优缺点分析

**优点：**
- ✅ 官方支持，稳定可靠
- ✅ 速度快，几秒内完成
- ✅ 数据结构规范
- ✅ 支持批量获取统计信息

**缺点：**
- ❌ 需要申请 API Key
- ❌ 有每日配额限制
- ❌ 不支持私有 Playlist

---

## 方案二：yt-dlp 工具

### 2.1 方案原理

yt-dlp 是一个开源的 YouTube 下载工具，可以提取视频元数据而不下载视频。

**工作流程：**

```
1. 安装 yt-dlp 库
   ↓
2. 使用 extract_info() 提取 Playlist 信息
   ↓
3. 遍历 entries 获取每个视频信息
   ↓
4. 格式化并保存数据
```

### 2.2 安装 yt-dlp

```bash
# 使用 pip 安装
pip install yt-dlp

# 或使用 conda
conda install -c conda-forge yt-dlp
```

### 2.3 具体实现代码

```python
import yt_dlp
import json
from datetime import datetime

class YtDlpFetcher:
    """yt-dlp 抓取器"""

    def __init__(self):
        self.ydl_opts = {
            'quiet': True,              # 静默模式
            'no_warnings': True,        # 不显示警告
            'extract_flat': False,      # 获取详细信息（不设为 True）
            'ignoreerrors': True,       # 忽略错误继续
            'no_color': True,          # 不使用颜色输出
        }

    def fetch_playlist(self, playlist_url):
        """
        获取 Playlist 所有视频

        Args:
            playlist_url: Playlist URL

        Returns:
            list: 视频信息列表
        """
        videos = []

        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            print("正在提取 Playlist 信息...")

            # 提取 Playlist 信息
            playlist_info = ydl.extract_info(playlist_url, download=False)

            if not playlist_info or 'entries' not in playlist_info:
                print("错误: 无法获取 Playlist 信息")
                return None

            total = len(playlist_info['entries'])
            print(f"发现 {total} 个视频\n")

            # 遍历每个视频
            for idx, entry in enumerate(playlist_info['entries'], 1):
                if not entry:
                    print(f"[{idx}/{total}] 跳过（无效视频）")
                    continue

                video_id = entry.get('id', '')
                title = entry.get('title', '')

                print(f"[{idx}/{total}] {title}")

                # 构建视频信息
                video_info = {
                    'videoId': video_id,
                    'url': f'https://www.youtube.com/watch?v={video_id}',
                    'title': title,
                    'description': entry.get('description', ''),
                    'channelTitle': entry.get('uploader', '') or entry.get('channel', ''),
                    'channelId': entry.get('channel_id', ''),
                    'publishedAt': self._format_date(entry.get('upload_date', '')),
                    'thumbnails': self._extract_thumbnails(entry),
                    'position': idx - 1,
                    'duration': entry.get('duration', 0),
                    'viewCount': entry.get('view_count', 0),
                    'likeCount': entry.get('like_count', 0),
                }

                videos.append(video_info)

                # 进度提示
                if idx % 10 == 0:
                    print(f"  进度: {idx}/{total}\n")

        return videos

    def _format_date(self, upload_date):
        """格式化日期为 ISO 8601"""
        if not upload_date:
            return ''

        try:
            # yt-dlp 返回格式: YYYYMMDD
            date_obj = datetime.strptime(str(upload_date), '%Y%m%d')
            return date_obj.isoformat() + 'Z'
        except:
            return ''

    def _extract_thumbnails(self, entry):
        """提取缩略图 URL"""
        thumbnails = {}

        # yt-dlp 返回的缩略图列表
        thumb_list = entry.get('thumbnails', [])

        if thumb_list:
            # 取最高质量的缩略图
            thumbnails['default'] = thumb_list[0].get('url', '')
            thumbnails['medium'] = thumb_list[0].get('url', '')
            thumbnails['high'] = thumb_list[-1].get('url', '') if len(thumb_list) > 1 else thumb_list[0].get('url', '')
        else:
            # 备用方案：使用标准缩略图 URL
            video_id = entry.get('id', '')
            if video_id:
                thumbnails['default'] = f'https://i.ytimg.com/vi/{video_id}/default.jpg'
                thumbnails['medium'] = f'https://i.ytimg.com/vi/{video_id}/mqdefault.jpg'
                thumbnails['high'] = f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
                thumbnails['maxres'] = f'https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg'

        return thumbnails

# 使用示例
if __name__ == '__main__':
    PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLxxxxxxxxxxx'

    fetcher = YtDlpFetcher()
    videos = fetcher.fetch_playlist(PLAYLIST_URL)

    if videos:
        # 保存结果
        with open('playlist_ytdlp_result.json', 'w', encoding='utf-8') as f:
            json.dump({
                'metadata': {
                    'totalVideos': len(videos),
                    'method': 'yt-dlp'
                },
                'videos': videos
            }, f, ensure_ascii=False, indent=2)

        print(f"\n成功抓取 {len(videos)} 个视频！")
```

### 2.4 优缺点分析

**优点：**
- ✅ 无需 API Key
- ✅ 无配额限制
- ✅ 支持私有 Playlist（需 cookies）
- ✅ 可获取更多统计信息（观看数、点赞数）
- ✅ 支持多种视频平台

**缺点：**
- ❌ 速度较慢（逐个抓取）
- ❌ 可能被 YouTube 限流
- ❌ 需要定期更新以应对 YouTube 变化
- ❌ 依赖第三方库

---

## 方案三：混合方案（推荐）

### 3.1 方案设计

结合两种方案的优点，实现智能切换：

**策略：**
1. **优先使用 API**（快速、稳定）
2. **API 失败时降级到 yt-dlp**（无限制）
3. **支持手动选择**（根据实际需求）

### 3.2 实现代码

（已在 `fetch_youtube_playlist.py` 中实现，这里提供核心逻辑）

```python
class HybridFetcher:
    """混合抓取器"""

    def __init__(self, api_key=None):
        self.api_key = api_key
        self.api_fetcher = YouTubeAPIFetcher(api_key) if api_key else None
        self.ytdlp_fetcher = YtDlpFetcher()

    def fetch_playlist(self, playlist_url, prefer_api=True):
        """
        混合方案抓取

        Args:
            playlist_url: Playlist URL
            prefer_api: 是否优先使用 API（默认 True）

        Returns:
            list: 视频信息列表
        """
        videos = None

        if prefer_api and self.api_fetcher:
            print("方案1: 尝试使用 YouTube Data API v3...")
            try:
                playlist_id = self.api_fetcher.extract_playlist_id(playlist_url)
                videos = self.api_fetcher.fetch_playlist(playlist_id)

                if videos:
                    print(f"✅ API 方案成功，获取 {len(videos)} 个视频\n")
                    return videos
            except Exception as e:
                print(f"❌ API 方案失败: {e}\n")

        # 降级到 yt-dlp
        print("方案2: 使用 yt-dlp...")
        try:
            videos = self.ytdlp_fetcher.fetch_playlist(playlist_url)

            if videos:
                print(f"✅ yt-dlp 方案成功，获取 {len(videos)} 个视频\n")
                return videos
        except Exception as e:
            print(f"❌ yt-dlp 方案失败: {e}\n")

        # 两种方案都失败
        if prefer_api and self.api_fetcher:
            print("⚠️  两种方案均失败")
        else:
            print("❌ yt-dlp 方案失败")

        return None
```

### 3.3 优势

- ✅ **自动降级**：API 失败自动切换
- ✅ **效率最优**：优先使用快速方案
- ✅ **容错性强**：单点故障不影响整体
- ✅ **灵活配置**：可手动选择方案

---

## API Key 申请详细教程

### 步骤 1：访问 Google Cloud Console

打开浏览器，访问：https://console.cloud.google.com/

### 步骤 2：创建新项目

1. 点击顶部导航栏的**项目下拉菜单**
2. 点击右上角的**"新建项目"**按钮
3. 输入项目名称（例如：`youtube-playlist-fetcher`）
4. 点击**"创建"**按钮
5. 等待项目创建完成（约 10-30 秒）

### 步骤 3：启用 YouTube Data API v3

1. 确保已选择刚创建的项目
2. 在左侧菜单选择**"API 和服务"** → **"库"**
3. 在搜索框输入：`YouTube Data API v3`
4. 点击搜索结果中的**"YouTube Data API v3"**
5. 点击**"启用"**按钮
6. 等待 API 启用完成

### 步骤 4：创建 API 凭据

1. 在左侧菜单选择**"API 和服务"** → **"凭据"**
2. 点击顶部的**"创建凭据"**按钮
3. 选择**"API 密钥"**
4. 系统会生成一个 API 密钥，复制并保存好

**示例 API Key 格式：**
```
AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 步骤 5：限制 API 密钥（可选但推荐）

1. 在生成 API 密钥的弹窗中，点击**"限制密钥"**
2. 在"API 限制"部分，选择**"限制密钥"**
3. 在下拉菜单中选择**"YouTube Data API v3"**
4. 点击**"保存"**

### 步骤 6：查看配额

1. 在左侧菜单选择**"API 和服务"** → **"配额"**
2. 搜索：`YouTube Data API v3`
3. 查看每日配额：默认 **10,000 units/天**

### 步骤 7：使用 API Key

将 API Key 添加到代码中：

```python
# 方法1：直接写入代码
API_KEY = 'AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'

# 方法2：使用环境变量（推荐）
import os
API_KEY = os.getenv('YOUTUBE_API_KEY')

# 方法3：从配置文件读取
import json
with open('config.json', 'r') as f:
    config = json.load(f)
    API_KEY = config['youtube_api_key']
```

### 配额提升（可选）

如果每日 10,000 units 不够用：

1. 访问：https://console.cloud.google.com/apis/api/youtube.googleapis.com/quotas
2. 点击**"申请配额增加"**
3. 填写申请表单（说明用途）
4. 等待 Google 审核（通常 1-3 个工作日）

---

## 私有 Playlist 抓取方案

### 7.1 问题说明

**YouTube Data API v3** 不支持私有 Playlist，会返回以下错误：

```json
{
  "error": {
    "code": 404,
    "message": "The playlist identified with the request's playlistId parameter cannot be found."
  }
}
```

### 7.2 解决方案：使用 yt-dlp + Cookies

#### 步骤 1：导出浏览器 Cookies

使用浏览器插件导出 cookies：

**Chrome/Edge：**
- 安装插件：[Get cookies.txt LOCALLY](https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
- 访问 YouTube 并登录
- 点击插件图标 → 下载 `cookies.txt`

**Firefox：**
- 安装插件：[cookies.txt](https://addons.mozilla.org/en-US/firefox/addon/cookies-txt/)
- 访问 YouTube 并登录
- 点击插件图标 → 导出 Cookies

#### 步骤 2：使用 Cookies 抓取

```python
class YtDlpPrivateFetcher:
    """yt-dlp 私有 Playlist 抓取器"""

    def __init__(self, cookies_file):
        self.ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,
            'cookiefile': cookies_file,  # 关键：指定 cookies 文件
        }

    def fetch_private_playlist(self, playlist_url):
        """抓取私有 Playlist"""
        with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
            playlist_info = ydl.extract_info(playlist_url, download=False)

            # 后续处理同普通 Playlist
            videos = []
            for entry in playlist_info.get('entries', []):
                # ... 解析视频信息
                pass

            return videos

# 使用示例
fetcher = YtDlpPrivateFetcher('cookies.txt')
videos = fetcher.fetch_private_playlist('https://www.youtube.com/playlist?list=PLxxxxx')
```

### 7.3 注意事项

⚠️ **安全提示：**
- Cookies 包含登录凭证，**切勿泄露**
- 定期更新 Cookies（过期时间通常 1-30 天）
- 不要在公共代码仓库中上传 `cookies.txt`

⚠️ **限制：**
- 只能抓取你有权限访问的 Playlist
- YouTube 可能检测自动化行为并限流

---

## 完整代码实现

完整的、生产级代码已在以下文件中实现：

📁 **`fetch_youtube_playlist.py`**
- 包含所有三种方案
- 支持混合策略
- 完整的错误处理
- 进度显示
- 缩略图下载功能
- 数据统计输出

📁 **`link_mv_versions.py`**
- MV 版本关联功能
- 创作者信息提取
- 智能标题匹配

详细代码请参考项目文件。

---

## 使用示例

### 示例 1：使用 API 方案

```python
from fetch_youtube_playlist import YouTubePlaylistFetcher

# 创建抓取器（提供 API Key）
fetcher = YouTubePlaylistFetcher(api_key='YOUR_API_KEY')

# 抓取 Playlist
playlist_url = 'https://www.youtube.com/playlist?list=PLxxxxxxxxxxx'
videos = fetcher.fetch_playlist(playlist_url, use_api_first=True)

# 保存结果
fetcher.save_to_json('output.json')

# 下载缩略图
fetcher.download_thumbnails(output_dir='thumbnails', quality='high')
```

### 示例 2：使用 yt-dlp 方案

```python
from fetch_youtube_playlist import YouTubePlaylistFetcher

# 创建抓取器（不提供 API Key）
fetcher = YouTubePlaylistFetcher()

# 抓取 Playlist（自动使用 yt-dlp）
playlist_url = 'https://www.youtube.com/playlist?list=PLxxxxxxxxxxx'
videos = fetcher.fetch_playlist(playlist_url)

# 保存结果
fetcher.save_to_json('output.json')
```

### 示例 3：批量抓取多个 Playlist

```python
import time
from fetch_youtube_playlist import YouTubePlaylistFetcher

playlists = [
    'https://www.youtube.com/playlist?list=PLxxx1',
    'https://www.youtube.com/playlist?list=PLxxx2',
    'https://www.youtube.com/playlist?list=PLxxx3',
]

fetcher = YouTubePlaylistFetcher(api_key='YOUR_API_KEY')

for idx, playlist_url in enumerate(playlists, 1):
    print(f"\n处理第 {idx}/{len(playlists)} 个 Playlist...")

    videos = fetcher.fetch_playlist(playlist_url)

    if videos:
        output_file = f'playlist_{idx}.json'
        fetcher.save_to_json(output_file)

    # 避免请求过快
    time.sleep(2)
```

### 示例 4：提取创作者信息

```python
import json
import re

# 加载抓取的数据
with open('playlist_videos.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# 提取创作者信息
for video in data['videos']:
    description = video.get('description', '')

    # 匹配创作者模式
    patterns = [
        r'2DMV[:\s]+(.+?)(?:\n|$)',
        r'映像[:\s]+(.+?)(?:\n|$)',
        r'Movie[:\s]+(.+?)(?:\n|$)',
        r'動画[:\s]+(.+?)(?:\n|$)',
        r'アニメーション[:\s]+(.+?)(?:\n|$)',
    ]

    creators = []
    for pattern in patterns:
        matches = re.findall(pattern, description, re.MULTILINE | re.IGNORECASE)
        creators.extend(matches)

    if creators:
        print(f"{video['title']}:")
        for creator in creators:
            print(f"  - {creator.strip()}")
```

---

## 故障排除

### 问题 1：API 返回 403 错误

**错误信息：**
```json
{
  "error": {
    "code": 403,
    "message": "The request cannot be completed because you have exceeded your quota."
  }
}
```

**原因：** 超出每日配额限制

**解决方案：**
1. 等待配额重置（太平洋时间午夜）
2. 申请配额增加
3. 使用多个 API Key 轮换
4. 切换到 yt-dlp 方案

### 问题 2：yt-dlp 抓取失败

**错误信息：**
```
ERROR: Unable to download webpage: HTTP Error 429: Too Many Requests
```

**原因：** 被 YouTube 限流

**解决方案：**
1. 添加延迟（每次请求间隔 2-5 秒）
2. 使用代理 IP
3. 更新 yt-dlp 到最新版本：`pip install -U yt-dlp`
4. 使用 cookies 文件

### 问题 3：私有 Playlist 无法访问

**解决方案：**
1. 使用 yt-dlp + cookies 方案
2. 确保 cookies 未过期
3. 确认已登录有权限的账号

### 问题 4：缩略图下载失败

**原因：** URL 失效或网络问题

**解决方案：**
1. 检查网络连接
2. 使用代理
3. 重试失败的下载
4. 使用备用缩略图 URL 格式：
   ```python
   f'https://i.ytimg.com/vi/{video_id}/hqdefault.jpg'
   ```

---

## 最佳实践

### 1. API 配额管理

```python
# 跟踪 API 使用量
class QuotaTracker:
    def __init__(self, daily_limit=10000):
        self.daily_limit = daily_limit
        self.used = 0

    def check_quota(self, cost):
        """检查配额是否足够"""
        if self.used + cost > self.daily_limit:
            return False
        return True

    def consume(self, cost):
        """消耗配额"""
        self.used += cost
        print(f"已使用配额: {self.used}/{self.daily_limit}")
```

### 2. 错误重试机制

```python
import time
from functools import wraps

def retry(max_attempts=3, delay=2):
    """重试装饰器"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"尝试 {attempt}/{max_attempts} 失败: {e}")
                    if attempt < max_attempts:
                        time.sleep(delay)
                    else:
                        raise
        return wrapper
    return decorator

@retry(max_attempts=3, delay=2)
def fetch_with_retry(url):
    # 抓取逻辑
    pass
```

### 3. 数据缓存

```python
import hashlib
import os
import json
from datetime import datetime, timedelta

class CachedFetcher:
    """带缓存的抓取器"""

    def __init__(self, cache_dir='cache', cache_ttl=3600):
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl  # 缓存有效期（秒）
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_key(self, url):
        """生成缓存键"""
        return hashlib.md5(url.encode()).hexdigest()

    def _is_cache_valid(self, cache_file):
        """检查缓存是否有效"""
        if not os.path.exists(cache_file):
            return False

        # 检查缓存时间
        mtime = os.path.getmtime(cache_file)
        age = datetime.now().timestamp() - mtime

        return age < self.cache_ttl

    def fetch_with_cache(self, url, fetcher_func):
        """使用缓存抓取"""
        cache_key = self._get_cache_key(url)
        cache_file = os.path.join(self.cache_dir, f'{cache_key}.json')

        # 尝试读取缓存
        if self._is_cache_valid(cache_file):
            print(f"使用缓存: {cache_file}")
            with open(cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)

        # 抓取新数据
        print(f"抓取新数据: {url}")
        data = fetcher_func(url)

        # 保存缓存
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return data
```

### 4. 日志记录

```python
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'fetcher_{datetime.now().strftime("%Y%m%d")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger('YouTubeFetcher')

# 使用日志
logger.info("开始抓取 Playlist")
logger.error(f"抓取失败: {error_message}")
logger.warning("配额即将用尽")
```

### 5. 环境变量管理

创建 `.env` 文件：
```bash
YOUTUBE_API_KEY=AIzaSyDxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
CACHE_TTL=3600
MAX_RETRIES=3
```

使用 `python-dotenv` 加载：
```python
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv('YOUTUBE_API_KEY')
CACHE_TTL = int(os.getenv('CACHE_TTL', 3600))
MAX_RETRIES = int(os.getenv('MAX_RETRIES', 3))
```

---

## 总结

### 方案选择建议

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| **公开 Playlist，频繁抓取** | API v3 | 快速、稳定、无限流风险 |
| **公开 Playlist，一次性抓取** | yt-dlp | 无需 API Key，简单直接 |
| **私有 Playlist** | yt-dlp + Cookies | 唯一可行方案 |
| **大规模批量抓取** | 混合方案 | API 用尽后降级 yt-dlp |
| **需要统计信息** | yt-dlp 或 API videos.list | yt-dlp 自动包含，API 需额外调用 |
| **生产环境** | 混合方案 + 缓存 + 重试 | 容错性强，效率高 |

### 关键要点

✅ **优先使用官方 API**（如果可以申请）
✅ **实现降级机制**（API 失败时使用 yt-dlp）
✅ **添加缓存**（避免重复抓取）
✅ **错误重试**（提高成功率）
✅ **日志记录**（便于追踪问题）
✅ **尊重配额限制**（避免滥用）

---

## 附录

### 附录 A：常见错误码

| 错误码 | 含义 | 解决方案 |
|-------|------|---------|
| 400 | 请求参数错误 | 检查 Playlist ID 格式 |
| 403 | 配额超限 | 等待重置或切换方案 |
| 404 | Playlist 不存在 | 检查 URL 或权限 |
| 429 | 请求过多 | 添加延迟或使用代理 |
| 500 | 服务器错误 | 重试或稍后再试 |

### 附录 B：有用的链接

- **YouTube Data API 文档**: https://developers.google.com/youtube/v3
- **yt-dlp GitHub**: https://github.com/yt-dlp/yt-dlp
- **Google Cloud Console**: https://console.cloud.google.com/
- **API 配额说明**: https://developers.google.com/youtube/v3/getting-started#quota

---

**文档版本：** 1.0.0
**最后更新：** 2026-01-22
**作者：** Claude Sonnet 4.5
