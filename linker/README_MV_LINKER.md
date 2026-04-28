# MV 版本关联工具

## 📖 功能介绍

这个工具可以将 `all_musics.json` 中的歌曲数据与 YouTube Playlist 中的 MV 视频进行智能关联，支持：

- ✅ **通过 musicId 关联**：一首歌对应多个 MV 版本
- ✅ **智能标题匹配**：支持模糊匹配和相似度计算
- ✅ **自动版本分类**：识别游戏版、原作者版、电影版等
- ✅ **提取创作者信息**：从描述中自动提取动画制作者
- ✅ **两种输出格式**：嵌套结构 + 关系型结构

---

## 🎯 数据结构设计

### 方案一：嵌套结构（推荐用于前端展示）

```json
{
  "metadata": {
    "generatedAt": "2026-01-22T16:00:00",
    "totalMusics": 631,
    "totalMvVersions": 850,
    "dataFormat": "nested"
  },
  "musics": [
    {
      "musicId": 181,
      "title": "群青讃歌",
      "titlePronunciation": "ぐんじょうさんか",
      "artist": {
        "composer": "Eve",
        "lyricist": "Eve",
        "arranger": "Numa"
      },
      "mvVersions": [
        {
          "versionId": "mv_181_001",
          "versionName": "1周年アニバーサリー版",
          "versionType": "game_anniversary",
          "versionTypeDisplay": "周年纪念版",
          "priority": 1,
          "youtube": {
            "videoId": "MxT59XJXMnU",
            "url": "https://www.youtube.com/watch?v=MxT59XJXMnU",
            "title": "1周年アニバーサリーソング『群青讃歌』",
            "description": "...",
            "channelTitle": "プロジェクトセカイ",
            "publishedAt": "2021-09-30T12:00:00Z",
            "thumbnails": { ... }
          },
          "creators": {
            "animation_studio": "南方研究所／SCOOTER FILMS",
            "director": "南方研究所",
            "animator": "くっか"
          },
          "similarity": 0.95
        },
        {
          "versionId": "mv_181_002",
          "versionName": "Eve Official MV",
          "versionType": "original_artist",
          "versionTypeDisplay": "原作者官方版",
          "priority": 2,
          "youtube": { ... },
          "creators": { ... }
        }
      ],
      "statistics": {
        "totalMvVersions": 3,
        "hasOriginalArtistMv": true,
        "hasMovieVersion": true
      }
    }
  ]
}
```

### 方案二：关系型结构（推荐用于数据库）

**musics 表：**
```json
{
  "musics": [
    {
      "musicId": 181,
      "title": "群青讃歌",
      "artist": { ... },
      "statistics": { ... }
    }
  ]
}
```

**mvVersions 表：**
```json
{
  "mvVersions": [
    {
      "versionId": "mv_181_001",
      "musicId": 181,  // 外键
      "versionName": "1周年アニバーサリー版",
      "versionType": "game_anniversary",
      "youtube": { ... },
      "creators": { ... }
    }
  ]
}
```

---

## 🚀 快速使用

### 1. 运行脚本

```bash
cd "c:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database\sekai-master-db-diff-main"

python link_mv_versions.py
```

### 2. 输入文件路径

```
请输入 all_musics.json 路径: extracted/20260122_111229_all_musics/all_musics.json
请输入 YouTube Playlist JSON 路径: playlist_videos_20260122_154134.json
```

### 3. 查看结果

生成两个文件：
- `linked_mv_versions_nested_*.json` - 嵌套结构
- `linked_mv_versions_relational_*.json` - 关系型结构

---

## 📋 版本类型分类

| 类型代码 | 显示名称 | 说明 | 示例 |
|---------|---------|------|------|
| `game_original` | 游戏内原版 | 游戏内默认 MV | 普通游戏 MV |
| `game_anniversary` | 周年纪念版 | 周年活动特别版 | 1周年アニバーサリー |
| `game_event` | 活动限定版 | 特定活动版本 | イベント限定 |
| `original_artist` | 原作者官方版 | 原曲作者官方 MV | Eve Official MV |
| `movie_version` | 电影版 | 剧场版 MV | 劇場版プロジェクトセカイ |
| `sekai_version` | SEKAI版 | SEKAI 特别版 | SEKAIver. |
| `unit_version` | 组合版本 | 特定组合演唱版 | Leo/need ver. |
| `character_version` | 角色版本 | 特定角色版 | ミクver. |
| `collaboration` | 联动版本 | 跨作品联动 | × コラボ |
| `other` | 其他版本 | 未分类版本 | - |

---

## 🔧 高级功能

### 自定义相似度阈值

编辑 `link_mv_versions.py`，修改 `similarity_threshold` 参数：

```python
# 默认 0.6（60% 相似度）
linker.link_versions(similarity_threshold=0.6)

# 更严格的匹配（推荐 0.7-0.8）
linker.link_versions(similarity_threshold=0.75)

# 更宽松的匹配（可能产生误匹配）
linker.link_versions(similarity_threshold=0.5)
```

### 作为 Python 模块使用

```python
from link_mv_versions import MVVersionLinker

# 创建关联器
linker = MVVersionLinker(
    all_musics_path='path/to/all_musics.json',
    youtube_playlist_path='path/to/playlist.json'
)

# 加载数据
linker.load_data()

# 关联版本
linked_data = linker.link_versions(similarity_threshold=0.6)

# 打印统计
linker.print_statistics()

# 保存结果
linker.save_to_json('output.json', format_type='nested')
```

### 提取特定信息

```python
# 查找有多个版本的歌曲
multi_version_songs = [
    music for music in linked_data
    if music['statistics']['totalMvVersions'] > 1
]

# 查找有电影版的歌曲
movie_version_songs = [
    music for music in linked_data
    if music['statistics']['hasMovieVersion']
]

# 统计每个创作者的作品数
from collections import Counter
all_creators = []
for music in linked_data:
    for mv in music['mvVersions']:
        creators = mv.get('creators', {})
        for creator_type, creator_name in creators.items():
            all_creators.append(creator_name)

creator_counts = Counter(all_creators)
print("Top 10 创作者:")
for creator, count in creator_counts.most_common(10):
    print(f"{creator}: {count} 个作品")
```

---

## 🎨 匹配逻辑说明

### 匹配优先级

1. **URL 精确匹配**（最高优先级）
   - 比对 `music.originalVideoLink` 和 `video.url`
   - 100% 准确

2. **标题相似度匹配**
   - 使用 SequenceMatcher 计算相似度
   - 阈值：默认 60%

3. **标题包含匹配**
   - 检查一个标题是否包含在另一个中
   - 适用于版本标题包含基础标题的情况

### 标题标准化

为了提高匹配准确性，标题会被标准化：
- 移除空格、连字符、下划线
- 转换为小写
- 移除版本标识（MV、ver.、version 等）

示例：
```
原标题: "群青讃歌 - Eve MV"
标准化: "群青讃歌eve"

原标题: "1周年アニバーサリーソング『群青讃歌』"
标准化: "1周年アニバーサリーソング群青讃歌"
```

---

## 📊 输出统计示例

```
╔══════════════════════════════════════════════════════════╗
║                    📊 关联统计                           ║
╚══════════════════════════════════════════════════════════╝

总歌曲数: 631
有 MV 的歌曲: 420 (66.6%)
有多版本 MV 的歌曲: 85 (13.5%)
MV 版本总数: 550
平均每首歌 MV 数: 0.87

MV 版本类型分布:
  - 游戏内原版: 320
  - 原作者官方版: 150
  - 周年纪念版: 45
  - 电影版: 12
  - 组合版本: 15
  - 其他版本: 8

多版本 MV 歌曲 (前10):
  - 群青讃歌: 3 个版本
  - Tell Your World: 2 个版本
  - ワールドイズマイン: 2 个版本
  ...
```

---

## ⚠️ 注意事项

### 匹配准确性

- **相似度阈值**：建议设置 0.6-0.8 之间
  - 过低：可能产生错误匹配
  - 过高：可能漏掉正确匹配

- **手动验证**：对于重要数据，建议抽样检查匹配结果

### 数据质量

- **YouTube 数据**：确保 Playlist 包含完整的视频信息
- **all_musics.json**：确保标题准确无误
- **描述信息**：创作者提取依赖于描述格式的一致性

### 性能考虑

- 631 首歌 × 240 个视频 ≈ 150,000 次比对
- 预计处理时间：30-60 秒
- 内存占用：约 50-100 MB

---

## 🛠️ 故障排除

### Q1: 匹配数量过少

**原因**：相似度阈值过高
**解决**：降低阈值到 0.5-0.6

### Q2: 出现错误匹配

**原因**：相似度阈值过低
**解决**：提高阈值到 0.7-0.8

### Q3: 无法提取创作者信息

**原因**：视频描述格式不统一
**解决**：
1. 检查描述中的创作者标识格式
2. 在 `extract_creators_from_description()` 中添加新的正则模式

### Q4: 文件路径错误

**原因**：Windows 路径包含反斜杠
**解决**：使用正斜杠或双反斜杠
```python
# 正确
"c:/Users/xxx/file.json"
"c:\\Users\\xxx\\file.json"

# 错误
"c:\Users\xxx\file.json"
```

---

## 📚 扩展功能建议

### 1. 添加手动映射

对于无法自动匹配的歌曲，可以手动指定：

```python
MANUAL_MAPPINGS = {
    181: [  # musicId
        'MxT59XJXMnU',  # videoId
        'sgZjbk9eH6g',
    ],
    42: ['xxxxxxxxxxx']
}
```

### 2. 导出为数据库

```python
import sqlite3

# 创建数据库
conn = sqlite3.connect('sekai_2dmv.db')

# 创建表
conn.execute('''
CREATE TABLE musics (
    music_id INTEGER PRIMARY KEY,
    title TEXT,
    composer TEXT
)
''')

conn.execute('''
CREATE TABLE mv_versions (
    version_id TEXT PRIMARY KEY,
    music_id INTEGER,
    version_name TEXT,
    youtube_url TEXT,
    FOREIGN KEY (music_id) REFERENCES musics(music_id)
)
''')

# 插入数据
for music in linked_data:
    conn.execute('INSERT INTO musics VALUES (?, ?, ?)',
                (music['musicId'], music['title'], music['artist']['composer']))

    for mv in music['mvVersions']:
        conn.execute('INSERT INTO mv_versions VALUES (?, ?, ?, ?)',
                    (mv['versionId'], music['musicId'],
                     mv['versionName'], mv['youtube']['url']))

conn.commit()
```

### 3. Web 界面展示

使用生成的 JSON 数据，可以轻松创建：
- 歌曲列表页（显示 MV 数量）
- 歌曲详情页（显示所有版本）
- 创作者页面（显示创作者作品列表）
- 版本对比页（对比不同版本）

---

## 🎉 示例用例

### 用例1：构建 2DMV 数据库网站

```
1. 抓取官方 Playlist → playlist_videos.json
2. 关联 MV 版本 → linked_mv_versions.json
3. 前端加载 JSON → 展示歌曲和多版本 MV
4. 点击歌曲 → 显示所有版本 + 创作者信息
```

### 用例2：统计创作者贡献

```python
# 找出最多产的动画师
from collections import Counter

animators = []
for music in linked_data:
    for mv in music['mvVersions']:
        if 'animator' in mv.get('creators', {}):
            animators.append(mv['creators']['animator'])

top_animators = Counter(animators).most_common(10)
```

### 用例3：版本对比分析

```python
# 找出游戏版和原作者版都有的歌曲
dual_version_songs = []
for music in linked_data:
    has_game = any(mv['versionType'] == 'game_original' for mv in music['mvVersions'])
    has_artist = any(mv['versionType'] == 'original_artist' for mv in music['mvVersions'])
    if has_game and has_artist:
        dual_version_songs.append(music)
```

---

**祝你数据关联愉快！** 🎵✨
