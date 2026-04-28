# 🎵 Project Sekai 2DMV Database - 使用说明

## 📋 项目简介

这是一个 Project Sekai 2DMV 视频数据库展示页面，可以从 YouTube 播放列表中获取视频数据并以美观的方式展示。

## 🧱 数据构建、Staff 与版本字段

### 重新构建数据库

在项目根目录运行：

```powershell
python scripts\build_database.py
```

这会更新以下核心输出：

- `output/database_v2.json`
- `output/video_staff_index.json`
- `output/staff_review.json`
- `output/original_mv_review.json`
- `output/aliases.json`

如果有手动补录视频，也会一并读取：

- `manual_data/manual_videos.json`
- `manual_data/video_sources.json`
- `manual_data/original_video_overrides.json`

### 自动刷新多个视频来源

现在 `scripts/auto_update.py` 支持按配置刷新多个外部视频来源，不再只固定抓官方 2DMV。

默认来源配置在：

- `manual_data/video_sources.json`

每个来源目前支持这些字段：

- `key`
  - 来源唯一标识，用来生成快照文件名
- `name`
  - 人类可读名称
- `kind`
  - 当前支持 `playlist`
- `enabled`
  - 是否启用该来源
- `url`
  - YouTube Playlist 地址
- `videoType`
  - 写入数据库时的视频类型默认值，例如 `official_2dmv`、`original_mv`
- `versionBase`
  - 写入数据库时的视频版本默认值，例如 `sekai`、`original`
- `extractors`
  - 预留给后续字段抽取器的来源标签，例如 `staff`、`performers`

运行：

```powershell
python scripts\auto_update.py
```

脚本会：

1. 检查主库更新
2. 按 `video_sources.json` 刷新每个来源的最新 Playlist 快照
3. 当音乐主库、来源配置、手动数据或任一来源快照发生变化时，自动重建输出

抓取下来的来源快照会保存在：

- `fetch_youtube_playlist/playlist_<sourceKey>_<timestamp>.json`

### 新增的 staff 数据结构

`output/database_v2.json` 现在包含两层 staff 信息：

- `songs[*].videos[*].staff`
  - 单个视频的 staff 解析结果
- `songs[*].staffSummary`
  - 同一首歌下所有视频的汇总结果

`videos[*].staff` 包含：

- `illustrators`
- `pvCreators`
- `otherRoles`
- `contributors`
- `unparsedLines`
- `unknownRoleLines`

`staffSummary` 包含：

- `illustrators`
- `pvCreators`
- `otherRoles`
- `allContributors`

### 新增的本家歌手字段

`output/database_v2.json` 现在还包含原曲 / 本家视频的歌手抽取结果：

- `songs[*].videos[*].performerExtraction`
  - 单个视频的歌手抽取结果，仅在来源配置启用了 `performers` 抽取器或手动补录提供了 `performers` 时出现
- `songs[*].performerSummary`
  - 同一首歌下所有视频汇总后的歌手列表

`performerExtraction` 结构：

- `performers`
- `source`
  - 例如：`manual`、`description_label`、`title_feat`
- `confidence`
- `matchedText`
- `needsReview`

### 新增的视频版本字段

`output/database_v2.json` 现在还包含多版本 MV 相关字段：

- `songs[*].videos[*].version`
  - 单个视频的版本信息
- `songs[*].videoVersionSummary`
  - 同一首歌下所有视频的版本汇总

`videos[*].version` 结构：

- `base`
  - 目前支持：`original`、`sekai`、`virtual_singer`、`another_vocal`、`unknown`
- `special`
  - 目前支持：`april_fool`
- `label`
  - 例如：`SEKAI ver`、`Virtual Singer ver`、`SEKAI ver / 愚人节版`

`videoVersionSummary` 结构：

- `bases`
- `special`
- `labels`

当前主页面 `index.html` 已接入基础版本展示和筛选。

### 审计文件用途

- `output/video_staff_index.json`
  - 扁平化 contributor 索引，适合统计每位 staff 的参与次数
- `output/staff_review.json`
  - 收集未识别角色与未成功解析的描述行，便于人工补录
- `output/original_mv_review.json`
  - 收集启用了 `performers` 抽取器、但暂时没能自动识别歌手的视频，便于人工复核

### 手工修正入口

如果某些角色或名字没有被正确归一化，可编辑：

- `manual_data/staff_role_aliases.json`
- `manual_data/staff_name_aliases.json`
- `manual_data/original_video_overrides.json`

修改后重新运行 `python scripts\build_database.py` 即可生效。

`original_video_overrides.json` 适合修正“视频已经在 playlist 里，但某些字段抽取不准”的情况，例如补 `performers`。推荐结构：

```json
{
  "videos": {
    "03IyS_9Dt0g": {
      "performers": ["初音ミク"]
    }
  }
}
```

这个文件不会替换整条原视频数据，只会按 `videoId` 覆盖你显式写入的字段。

### 手动补录视频入口

如果后续有一些视频没有出现在官方播放列表里，可以使用：

- `http://localhost:8000/manual_video_editor.html`

这个页面会：

- 读取 `manual_data/manual_videos.json`
- 读取 `manual_data/original_video_overrides.json`
- 读取 `output/original_mv_review.json` 作为待复核歌手队列
- 辅助搜索现有曲库并填写曲名
- 手动录入 YouTube 链接、标题、发布时间、描述等字段
- 支持手动指定 `本家 / SEKAI ver / Virtual Singer ver / Another Vocal / 愚人节版`
- 导出新的 `manual_videos.json`
- 导出新的 `original_video_overrides.json`

推荐流程：

1. 打开 `manual_video_editor.html`
2. 如果是缺失视频，就在“补录表单”里编辑并导出 `manual_videos.json`
3. 如果是已存在视频字段不准，就在“字段覆写表单”里编辑并导出 `original_video_overrides.json`
4. 用导出的文件覆盖 `manual_data/manual_videos.json` 或 `manual_data/original_video_overrides.json`
5. 运行 `python scripts\build_database.py`

构建脚本会自动把手动补录视频并入 `output/database_v2.json`，并按 `videoId` 去重。
如果视频本身已经存在于 playlist，只需要改 `manual_data/original_video_overrides.json`，不需要再补一整条 `manual_videos.json`。

## 🚀 快速开始

### 方法一：使用启动脚本（推荐）

1. **双击运行** `启动本地服务器.bat`
2. 等待服务器启动（会自动打开命令行窗口）
3. 在浏览器中访问：`http://localhost:8000`
4. 完成！你应该能看到视频数据库页面

### 方法二：手动启动服务器

```bash
# 在项目目录下打开命令行
cd "c:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database"

# 启动 Python HTTP 服务器
python -m http.server 8000

# 在浏览器访问
# http://localhost:8000
```

## ❓ 为什么需要本地服务器？

由于浏览器的**同源策略（CORS）**限制，直接双击打开 `index.html` 文件会导致：
- ❌ 无法加载外部 JSON 数据文件
- ❌ 看到"加载失败"错误提示

使用本地服务器可以：
- ✅ 正常加载 JSON 数据
- ✅ 完全避免跨域问题
- ✅ 模拟真实的网站运行环境

## 📂 项目结构

```
Project Sekai 2DMV Database/
├── index.html                          # 主页面（YouTube 数据库展示）
├── music_viewer.html                   # 音乐数据查看器
├── manual_video_editor.html            # 手动视频补录工具
├── start_server.bat                    # 启动服务器
├── 启动本地服务器.bat                    # 一键启动脚本
├── 启动JSON转CSV工具.bat                # JSON转CSV工具
├── README_使用说明.md                   # 本文件
├── docs/                               # 📚 文档
├── scripts/                            # 🔧 处理脚本
├── manual_data/                        # ✍️ 手工维护数据（别称 / 修正 / 手动补录视频）
├── output/                             # 📦 输出数据
├── Database/                           # 数据库
├── fetch_youtube_playlist/             # YouTube 播放列表抓取
├── fetch_original_videos/              # 原始视频抓取
├── extract_creators/                   # 创作者提取工具
├── linker/                             # MV 版本关联
├── sekai-master-db-diff-main/          # Master 数据库源
└── sekai viewer_json/                  # Sekai Viewer 资源
```

## 🔧 配置说明

### 更换数据源

如果你想使用不同的 JSON 数据文件，只需编辑 `index.html` 文件：

```javascript
// 找到这一行（大约在第 465 行）
const JSON_DATA_PATH = './fetch_youtube_playlist/playlist_videos_20260122_161800.json';

// 修改为你想要的文件路径
const JSON_DATA_PATH = './fetch_youtube_playlist/你的文件名.json';
```

### 更换服务器端口

如果 8000 端口被占用，可以修改 `启动本地服务器.bat`：

```batch
# 找到这一行
python -m http.server 8000

# 改为其他端口，例如 3000
python -m http.server 3000
```

## 🎨 功能特性

- 📺 **视频卡片展示** - 缩略图、标题、描述、频道等信息
- 🔍 **实时搜索** - 支持搜索标题、描述、频道名
- 📊 **多种排序** - 按位置、日期、标题排序
- 🎯 **字段筛选** - 可自定义显示/隐藏字段
- 🎭 **精美 UI** - 渐变背景、动画效果、响应式设计
- 🧑‍🎨 **Staff 结构化提取** - 自动识别插画、PV 制作与部分设计/动画相关 staff
- 🧾 **审计输出** - 自动生成 staff 扁平索引和待人工复核文件

## 🐛 常见问题

### 问题 1：看到"加载失败"错误

**原因**：直接双击打开了 HTML 文件，而不是通过服务器访问

**解决**：
1. 双击运行 `启动本地服务器.bat`
2. 在浏览器访问 `http://localhost:8000`

### 问题 2：提示"未找到 Python"

**原因**：系统未安装 Python 或未添加到环境变量

**解决**：
1. 下载 Python：https://www.python.org/downloads/
2. 安装时务必勾选 **"Add Python to PATH"**
3. 重启命令行/计算机

### 问题 3：端口 8000 被占用

**解决**：
- 编辑 `启动本地服务器.bat`，将 `8000` 改为其他端口（如 `3000`）
- 访问时使用新端口：`http://localhost:3000`

### 问题 4：JSON 文件路径错误

**解决**：
- 检查 `index.html` 中的 `JSON_DATA_PATH` 是否正确
- 确保 JSON 文件确实存在于指定路径

## 🌐 部署到线上

如果想部署到互联网，可以使用以下平台：

### GitHub Pages（推荐，免费）

1. 创建 GitHub 仓库
2. 上传所有文件
3. 在仓库设置中启用 GitHub Pages
4. 访问 `https://你的用户名.github.io/仓库名`

### 其他选择

- **Netlify** - 拖拽文件夹即可部署
- **Vercel** - 零配置部署
- **Cloudflare Pages** - 全球 CDN 加速

## 📝 许可证

© 2026 Project Sekai 2DMV Database | Created with ❤️

---

**提示**：如有任何问题，请检查浏览器控制台（F12）中的错误信息。
