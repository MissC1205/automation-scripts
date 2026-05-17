# 自动化脚本中心

服务器自动化脚本统一管理，方便修改、同步、备份。

## 目录结构

```
automation-scripts/
├── daily-info/         # 每日资讯推送相关
│   ├── ai_briefing.py
│   ├── ai_news_scraper.py
│   ├── fetch_ai_news.py
│   ├── weibo_scraper.py
│   ├── daily_briefing.sh
│   └── run_briefing.sh
│
├── github-tools/      # GitHub 相关工具
│   ├── github_search.py
│   ├── fetch_repos.sh
│   ├── search_github.sh
│   └── search_templates.sh
│
├── website/            # 网站部署和监控
│   ├── deploy.sh
│   ├── auto-deploy.sh
│   ├── heartbeat_monitor.sh
│   ├── icp-monitor.sh
│   └── fix_article_route.py
│
├── procurement/        # 采购单处理
│   ├── ocr_handwriting_search.py
│   └── run_ocr_search.sh
│
├── skills-hub/         # Hermes Agent Skills 相关
│   ├── skills_upgrade.py
│   ├── skills_store_cli.py
│   └── hermes-scripts/  # Hermes 自动化脚本
│       ├── auto_learn.py
│       └── heartbeat_v2.py
│
├── tools/              # 工具脚本（注：含密钥，不上传）
│   └── upload.py       # COS 图片上传（本地保留，不上传）
│
└── README.md
```

## 使用方法

### 克隆到本地/服务器

```bash
git clone https://github.com/MissC1205/automation-scripts.git
cd automation-scripts
```

### 同步最新代码

```bash
git pull origin main
```

### 修改后推送到 GitHub

```bash
git add .
git commit -m "描述你改了什么"
git push origin main
```

## 最近更新

- 2026-05-17：初始化仓库，整理所有服务器脚本