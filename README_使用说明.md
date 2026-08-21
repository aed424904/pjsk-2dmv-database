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
3. 当音乐主库、来源配置、手动数据或任一来源快照发生变化时，在临时目录重建并校验输出
4. 只有全部产物通过校验后才替换 `output/` 中的正式数据；失败时继续保留上一版

为防止 API 分页异常覆盖完整数据，新快照如果比当前有效快照骤减超过 20%，会被拒绝并保留旧快照。

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

- `http://localhost:8000/editor.html?tab=video`

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

1. 打开 `editor.html?tab=video`
2. 如果是缺失视频，就在“补录表单”里编辑并导出 `manual_videos.json`
3. 如果是已存在视频字段不准，就在“字段覆写表单”里编辑并导出 `original_video_overrides.json`
4. 用导出的文件覆盖 `manual_data/manual_videos.json` 或 `manual_data/original_video_overrides.json`
5. 运行 `python scripts\build_database.py`

构建脚本会自动把手动补录视频并入 `output/database_v2.json`，并按 `videoId` 去重。
如果视频本身已经存在于 playlist，只需要改 `manual_data/original_video_overrides.json`，不需要再补一整条 `manual_videos.json`。

同一个统一编辑器也提供别称维护，地址为 `http://localhost:8000/editor.html?tab=alias`。旧的 `manual_video_editor.html` 和 `alias_editor.html` 链接会自动跳转到对应标签页，已有书签无需修改。

### Staff 人工复核入口

打开 `http://localhost:8000/editor.html?tab=staff`，可以直接处理 `output/staff_review.json` 中的未知角色和未解析描述行。

页面支持：

- 按歌曲、视频、角色标签或原始描述搜索
- 按“未知角色 / 未解析行”和处理状态筛选
- 把原始角色标签映射为标准 Staff 角色
- 把同一 Staff 的不同署名归一为统一写法
- 忽略链接、宣传信息等明确无关的完整描述行
- 在手机端选择问题后自动定位到修正表单

完成复核后，根据修改类型导出：

- `staff_role_aliases.json`
- `staff_name_aliases.json`
- `staff_line_ignores.json`

用导出的文件替换 `manual_data/` 中的同名文件，再运行 `python scripts\build_database.py`。导出文件包含已有规则和本次修改，不是只包含增量。

### 浏览、筛选与分享

- `index.html` 是歌曲列表，可搜索歌名、创作者、别称、Staff 与版本，并按团队、MV 类型、歌声版本、视频版本和 Staff 字段筛选。
- `video_viewer.html` 是视频列表，可搜索视频标题、歌曲名、Staff 与频道，并按团队、视频类型、版本和频道筛选。
- 手机端点击搜索框下方的“筛选条件”即可打开完整筛选抽屉；底部按钮会实时显示当前结果数。
- 搜索、筛选和排序会自动写入浏览器网址。复制当前网址即可分享同一结果，刷新以及浏览器前进/后退也会恢复对应状态。

## 🚀 快速开始

### 方法一：使用启动脚本（推荐）

1. **双击运行** `启动本地服务器.bat`
2. 等待脚本生成安全的 `dist/` 站点目录并启动服务器
3. 在浏览器中访问：`http://localhost:8000`
4. 完成！你应该能看到视频数据库页面

### 方法二：手动启动服务器

```bash
# 在项目目录下打开命令行
cd "c:\Users\10693\Desktop\并非工作内容\Project Sekai 2DMV Database"

# 生成只包含网页运行所需文件的站点目录
python scripts/build_site.py

# 仅监听本机并只提供 dist 目录
python -m http.server 8000 --bind 127.0.0.1 --directory dist

# 在浏览器访问
# http://localhost:8000
```

### 自动浏览器验收

修改页面或数据后，可运行：

```powershell
npm run check:browser
```

该命令会自动构建 `dist/`，使用随机本地端口启动临时站点，检查歌曲搜索、排序、网址状态与展开，视频搜索与键盘操作，编辑器标签、Staff 复核与修正草稿、旧链接跳转，以及手机筛选抽屉、历史返回和视频卡片布局；结束后自动关闭浏览器与服务器。

首次在新环境使用时先运行 `npm install`。如果提示缺少 Chromium，再运行 `npx playwright install chromium`。

## ❓ 为什么需要本地服务器？

由于浏览器的**同源策略（CORS）**限制，直接双击打开 `index.html` 文件会导致：
- ❌ 无法加载外部 JSON 数据文件
- ❌ 看到"加载失败"错误提示

使用项目提供的本地服务器可以：
- ✅ 正常加载 JSON 数据
- ✅ 完全避免跨域问题
- ✅ 模拟真实的网站运行环境
- ✅ 不会公开 `.git`、备份、测试和构建脚本

## 📂 项目结构

```
Project Sekai 2DMV Database/
├── index.html                          # 主歌曲列表
├── video_viewer.html                   # 视频列表
├── editor.html                         # 统一编辑器（视频补录 / 别称编辑）
├── music_viewer.html                   # 旧歌曲链接兼容跳转页
├── manual_video_editor.html            # 旧视频编辑链接兼容跳转页
├── alias_editor.html                   # 旧别称编辑链接兼容跳转页
├── assets/                             # 三个主页面的样式、查看逻辑与编辑模块
├── package.json                        # 前端验收命令与 Playwright 版本
├── start_server.bat                    # 启动服务器
├── 启动本地服务器.bat                    # 一键启动脚本
├── 启动JSON转CSV工具.bat                # JSON转CSV工具
├── README_使用说明.md                   # 本文件
├── docs/                               # 📚 文档
├── dist/                               # 🌐 自动生成的安全站点目录（不提交 Git）
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

### 更换视频数据源

编辑 `manual_data/video_sources.json`，然后运行 `python scripts/auto_update.py`。主页面固定读取经过构建和校验的 `output/database_v2.json`，不再直接绑定某一份播放列表快照。

### 更换服务器端口

如果 8000 端口被占用，可以修改 `启动本地服务器.bat` 中服务器命令的端口：

```batch
# 找到这一行
python -m http.server 8000 --bind 127.0.0.1 --directory dist

# 改为其他端口，例如 3000
python -m http.server 3000 --bind 127.0.0.1 --directory dist
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

仓库内的 `.github/workflows/update-data.yml` 会运行测试、更新并校验数据、构建 `dist/`，随后只把 `dist/` 部署到 GitHub Pages。不要直接发布整个项目根目录。

### 其他选择

- **Netlify** - 拖拽文件夹即可部署
- **Vercel** - 零配置部署
- **Cloudflare Pages** - 全球 CDN 加速

## 📝 许可证

© 2026 Project Sekai 2DMV Database | Created with ❤️

---

**提示**：如有任何问题，请检查浏览器控制台（F12）中的错误信息。
