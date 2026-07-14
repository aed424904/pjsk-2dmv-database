# Project Sekai 2DMV Database — 实现进度报告

> 生成时间：2026-04-21

> 2026-07-14 更新：下方 4 月报告保留为历史记录；当前状态以本节为准。

## 2026-07-14 当前状态

- 数据库包含 341 个聚合歌曲条目、425 个唯一视频；结构与引用校验通过。
- 首页整合展示 699 首游戏歌曲；别称搜索、侧栏筛选、排序和详情展开已实现。
- 视频页以 `database_v2.json` 为唯一视频真源，显示 425 / 425 个视频，当前待关联数为 0。
- 已修复静态 JSON 被浏览器缓存后显示旧数据的问题：首页、歌曲页和视频页的动态数据请求均使用 `cache: 'no-store'`。
- 离线验证通过：52 个 `unittest`、Python `compileall`、`scripts/validate_data.py`。
- 浏览器抽查通过：别称“洛基”命中 `ロキ`；Leo/need 筛选得到 87 首；视频搜索 `CRASH THE PARTY` 得到 2 条；Enter 键可展开视频详情；未发现控制台错误。

### 尚未完成

1. 处理 `output/staff_review.json` 中 226 条 Staff 人工复核记录。
2. 完成移动端、全量筛选组合及性能指标的系统化浏览器验收。
3. 推送本地提交，然后验证 GitHub Actions 与 GitHub Pages 的线上运行状态。
4. 高级搜索面板仍为后续增强项，不阻塞当前版本发布。

中文服数据目录及其导出脚本/CSV、Leo/need 分析 CSV 和 `char_*.txt` 已确定为本地参考/分析文件，并通过 `.gitignore` 排除，不纳入正式仓库。

---

## 一、项目整体目标

将 YouTube 播放列表视频数据 + Sekai Viewer 游戏数据 + 手动维护数据 整合为**以歌曲为中心**的关系型数据库，并通过前端页面展示和搜索。

参考 [数据库重构实施方案.md](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/数据库重构实施方案.md)，计划分 **6 个阶段**实施。

---

## Staff 字段专项更新（2026-04-21）

### 本次新增内容

- `scripts/staff_extraction.py`
  - 新增 staff parser，负责把描述文本解析为标准化 contributor 记录
- `manual_data/staff_role_aliases.json`
  - 手工维护角色别名，优先级高于内置默认映射
- `manual_data/staff_name_aliases.json`
  - 手工维护人名归一化映射
- `tests/test_staff_extraction.py`
  - 新增 10 个单元测试，覆盖 taxonomy、行解析、song 汇总、审计导出

### 新增数据字段

- `output/database_v2.json`
  - `songs[*].videos[*].staff`
  - `songs[*].staffSummary`

`videos[*].staff` 结构：

- `illustrators`
- `pvCreators`
- `otherRoles`
- `contributors`
- `unparsedLines`
- `unknownRoleLines`

`staffSummary` 结构：

- `illustrators`
- `pvCreators`
- `otherRoles`
- `allContributors`

### 新增审计输出

- `output/video_staff_index.json`
  - 扁平 contributor 索引，适合统计与透视分析
- `output/staff_review.json`
  - 待人工复核的 `unknownRoleLines` / `unparsedLines`

### 当前覆盖情况（基于 2026-04-21 构建结果）

- 总视频数：253
- 识别到 `illustrator` 的视频：237
- 识别到 `pvCreator` 的视频：233
- 仅存在 `unknown` 角色的视频：2
- `video_staff_index.json` 行数：787
- `staff_review.json` 行数：66

### 已完成抽样核对

- `CRASH THE PARTY`
  - `illustrators = ["燠"]`
  - `pvCreators = ["筆者"]`
  - `otherRoles.illustrationAnimation = ["お菊"]`
- `傀儡のうつつ`
  - `illustrators = ["イワワ"]`
  - `pvCreators = ["omu"]`
- `告白`
  - `illustrators = ["カラスロ"]`
  - `pvCreators = ["春望かなめ"]`
- `透過する温度`
  - `illustrators = ["あさ"]`
  - `pvCreators = ["椎柚あげ(R11R)"]`
- `カラフルファンデーション`
  - `illustrators = ["秋鷲"]`
  - `pvCreators = ["椎柚あげ(R11R)"]`
  - `otherRoles.design = ["neybell"]`

### 已知限制

- 仍有一部分动画制作流程类标签会落入 `unknown`，例如：`原画`、`第二原画`、`アニメーションプロデューサー`
- 对这些残余标签的修正，优先通过 `manual_data/staff_role_aliases.json` 与 `manual_data/staff_name_aliases.json` 维护

---

## 二、各阶段完成情况

### ✅ 阶段一：数据准备

| 项目 | 状态 | 说明 |
|------|------|------|
| 目录结构创建 | ✅ 完成 | `manual_data/`、`scripts/`、[output/](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/json_to_csv.py#317-322)、`backup/` 均已创建 |
| [aliases.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/manual_data/aliases.json) | ✅ 完成 | 位于 [manual_data/aliases.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/manual_data/aliases.json)（1.3 KB，少量示例条目） |
| [corrections.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/manual_data/corrections.json) | ✅ 完成 | 位于 [manual_data/corrections.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/manual_data/corrections.json)（506 B） |

### ✅ 阶段二：构建脚本开发

| 项目 | 状态 | 说明 |
|------|------|------|
| [build_database.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/scripts/build_database.py) | ✅ 完成 | 425行，整合 YouTube + Sekai Viewer + 手动数据 → [database_v2.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/output/database_v2.json) |
| [build_musics_base.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/scripts/build_musics_base.py) | ✅ 完成 | 180行，从 Sekai 数据生成轻量级 [musics_base.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/output/musics_base.json)（全部歌曲基础信息） |
| [validate_data.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/scripts/validate_data.py) | ✅ 完成 | 数据验证脚本，检查结构完整性与引用关系 |

**已生成的数据文件：**

| 文件 | 大小 | 说明 |
|------|------|------|
| [output/database_v2.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/output/database_v2.json) | 632 KB | 包含歌曲 + 视频 + 标签的整合数据库 |
| [output/musics_base.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/output/musics_base.json) | 433 KB | 全部歌曲基础数据（不含 YouTube 视频） |
| [combined_music_data.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/combined_music_data.json) | 973 KB | 中间产物，合并多个 Sekai 源数据 |
| [Database/all_music.db](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/Database/all_music.db) | 2.2 MB | SQLite 数据库 |

### ✅ 阶段三：数据验证

| 项目 | 状态 | 说明 |
|------|------|------|
| [validate_data.py](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/scripts/validate_data.py) | ✅ 完成 | 支持元数据、歌曲、视频、引用完整性四项验证 |

### ⚠️ 阶段四：前端代码重构 — **部分完成**

| 项目 | 状态 | 说明 |
|------|------|------|
| [index.html](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/index.html)（旧版表格视图） | ✅ 存在 | 2921行，完整的搜索 / 筛选 / 排序 / 字段显示功能 |
| [music_viewer.html](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/music_viewer.html)（新版音乐列表视图） | ✅ 存在 | 931行，暗色主题，侧边栏筛选（团体/MV类型），以歌曲为中心展示 |
| 别称搜索功能 | ❌ **未集成** | 方案中规划了别称搜索，但前端尚未从 [database_v2.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/output/database_v2.json) 读取别称 |
| 数据源切换 | ⚠️ 待确认 | [index.html](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/index.html) 仍引用 `fetch_youtube_playlist/*.json`，尚未切换到 [database_v2.json](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/output/database_v2.json) |
| 搜索面板（高级搜索） | 📐 **仅设计** | [search_panel_design.md](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/search_panel_design.md) 完成了详细 UI 设计，但未实现代码 |

### ❌ 阶段五：测试与优化 — **部分完成**

| 项目 | 状态 | 说明 |
|------|------|------|
| 性能优化（[music_viewer.html](file:///c:/Users/10693/Desktop/%E5%B9%B6%E9%9D%9E%E5%B7%A5%E4%BD%9C%E5%86%85%E5%AE%B9/Project%20Sekai%202DMV%20Database/music_viewer.html)） | ✅ 完成 | 已做过分页、`backdrop-filter` 优化、CSS containment 等 |
| 功能测试清单 | ❌ 未执行 | 方案中列出了全套测试项，但尚未系统执行 |

### ❌ 阶段六：部署与上线 — **未开始**

| 项目 | 状态 | 说明 |
|------|------|------|
| Git 版本控制 | ❌ 未配置 | |
| GitHub Pages 部署 | ❌ 未部署 | |

---

## 三、已完成的辅助工具

| 工具 | 文件 | 说明 |
|------|------|------|
| YouTube 播放列表抓取 | [fetch_youtube_playlist.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/fetch_youtube_playlist/fetch_youtube_playlist.py) | API + yt-dlp 混合方案，已抓取数据 |
| 原曲视频信息抓取 | [fetch_original_videos.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/fetch_original_videos/fetch_original_videos.py) | 获取原版投稿视频信息 |
| 创作者信息提取 | [extract_creators.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/extract_creators/extract_creators.py) | 从视频描述提取动画师/插画师等 |
| MV 版本关联 | [link_mv_versions.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/linker/link_mv_versions.py) | 智能关联同一首歌的不同 MV 版本 |
| Sekai 数据提取 | [extract_music_data.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/extract_music_data.py) | 从 master DB 提取音乐数据，支持 JSON/CSV/SQL 导出 |
| 数据合并 | [combine_music_data.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/combine_music_data.py) | 合并多个 Sekai 源为统一 JSON |
| JSON→CSV 转换 | [json_to_csv.py](file:///c:/Users/10693/Desktop/并非工作内容/Project%20Sekai%202DMV%20Database/json_to_csv.py) | 带 Tkinter GUI 的转换工具 |

---

## 四、数据资产一览

| 数据源 | 路径 | 状态 |
|--------|------|------|
| YouTube 播放列表数据 | `fetch_youtube_playlist/playlist_videos_*.json` | ✅ 已采集（含缩略图） |
| Sekai Viewer 游戏数据 | `sekai viewer_json/`（16个文件） | ✅ 已准备 |
| Sekai Master DB Diff | `sekai-master-db-diff-main/`（411项） | ✅ 已准备 |
| 原曲视频数据 | `fetch_original_videos/output/` | ✅ 已采集 |
| 创作者提取结果 | `extract_creators/output/` | ✅ 已提取 |

---

## 五、总结与建议

### 当前整体进度：约 **65%**

```
阶段一 数据准备     ████████████████████ 100%
阶段二 脚本开发     ████████████████████ 100%
阶段三 数据验证     ████████████████████ 100%
阶段四 前端重构     ████████░░░░░░░░░░░░  40%
阶段五 测试优化     ██████░░░░░░░░░░░░░░  30%
阶段六 部署上线     ░░░░░░░░░░░░░░░░░░░░   0%
```

### 关键待完成项

1. **前端数据源切换**：`index.html` 或 `music_viewer.html` 需要切换到 `database_v2.json` 数据源
2. **别称搜索集成**：方案已设计完成，代码尚未实现
3. **高级搜索面板**：已完成 UI 设计（含角色筛选、版本类型筛选等），需要编码实现
4. **系统测试**：功能测试清单已列出，需逐项验证
5. **部署上线**：Git 初始化 + GitHub Pages 部署
