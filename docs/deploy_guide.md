# 分发与自动更新指南

## 1. 推送到 GitHub

```bash
# 在项目目录打开终端
git init
git add .
git commit -m "初始化项目"
git branch -M main

# 先在 GitHub 网页上创建一个新仓库（如 pjsk-2dmv-db），然后：
git remote add origin https://github.com/你的用户名/仓库名.git
git push -u origin main
```

## 2. 设置 YouTube API Key

仓库页面 → Settings → Secrets and variables → Actions → **New repository secret**：

- Name：`YOUTUBE_API_KEY`
- Value：你的 YouTube API Key

## 3. 开启 GitHub Pages

Settings → Pages：

- Source 选 `Deploy from a branch`
- Branch 选 `gh-pages` → `/ (root)` → Save

一分钟后访问 `https://你的用户名.github.io/仓库名/` 即可。

## 4. 手动触发验证

Actions 标签页 → 左侧选「定时更新数据并部署」→ Run workflow → 确认运行。

---

## 配额说明

| 操作 | API 调用 | 配额 |
|---|---|---|
| 抓取播放列表 | ~10 次 | 10 |
| 补全播放量/频道 | ~9 次 | 9 |
| **每次合计** | ~19 次 | **19 / 10,000** |

每天 10,000 配额，每次只用 0.2%，一天跑一次完全无压力。
