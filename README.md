# BeautyIntel Brief

Beauty Intelligence Morning Brief 是一个面向品牌市场部的美妆行业新闻早报推送器 MVP。第一版聚焦读取 `sources.yaml` 和 `sample_manual_import.csv`，完成分类、打分、风险识别、Markdown/HTML 早报生成，以及 dry-run 推送。

## 功能列表

- 数据源配置：支持 RSS、网页占位、人工 CSV、placeholder。
- 新闻处理：去重、规则分类、中文摘要、风险识别、重要性评分。
- 早报输出：生成 Markdown 与 HTML，默认保存到 `data/reports/`。
- API：`/health`、`/sources`、`/items`、`/reports`、`/jobs/ingest`、`/jobs/generate-report`。
- 推送：飞书、Slack、Email、通用 webhook，占位且支持 dry-run。
- 测试：覆盖去重、分类、评分、CSV 导入和报告生成。

## 目录结构

```text
app/                 后端代码
config/              数据源、品牌、关键词、评分配置
prompts/             AI 分类和摘要 prompt
data/demo/           示例手动导入数据
data/reports/        生成的早报
tests/               pytest 测试
```

## 快速开始

```bash
make install
make init-db
make ingest-demo
make brief-demo
make test
make run-api
```

等价命令：

```bash
py -3 -m app.cli init-db
py -3 -m app.cli ingest
py -3 -m app.cli generate-report --today
py -3 -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## 环境变量

复制 `.env.example` 为 `.env` 后按需配置：

- `DATABASE_URL`：默认 `sqlite:///./data/beautyintel.db`
- `BRIEF_TIMEZONE`：默认 `Asia/Shanghai`
- `OPENAI_API_KEY`、`OPENAI_MODEL`：预留 AI 接入；未配置时使用规则摘要和分类。
- `LARK_WEBHOOK_URL`、`SLACK_WEBHOOK_URL`、`GENERIC_WEBHOOK_URL`
- `SMTP_HOST`、`SMTP_PORT`、`SMTP_USER`、`SMTP_PASSWORD`、`EMAIL_FROM`、`EMAIL_TO`

## 数据源配置

数据源在 `config/sources.yaml`。MVP 默认启用人工 CSV，网页和国际媒体保留 placeholder。对没有 RSS/API 的来源，请使用官方 API、合规第三方接口或人工导入，不绕过登录、验证码、反爬或付费墙。

添加 RSS 数据源：

```yaml
- name: "示例 RSS"
  source_type: "rss"
  url: "https://example.com/feed.xml"
  homepage_url: "https://example.com"
  language: "zh"
  country_or_region: "CN"
  category: "market_overview"
  credibility_level: "industry_media"
  enabled: true
  fetch_interval_minutes: 1440
  tags: ["行业", "美妆"]
```

添加网页数据源：先配置为 `webpage` 或 `placeholder`，生产接入时应遵守 robots、网站条款和访问频率。正文提取失败时，系统可使用标题、摘要和 metadata 低置信度处理。

## 人工 CSV 导入

示例文件：`data/demo/sample_manual_import.csv`。字段包括：

`title,url,source_name,published_at,category,raw_excerpt,content_text,related_brands,related_platforms,tags`

适合导入小红书、抖音、微博、TikTok、Instagram、YouTube 等平台的人工整理趋势或合规第三方数据。

## 品牌和竞品

在 `config/brands.yaml` 配置自有品牌、核心竞品、观察品牌和渠道词。评分会基于自有品牌、核心竞品、重点品类、渠道、功效词提高相关性。

## 运行每日早报

```bash
py -3 -m app.cli ingest
py -3 -m app.cli generate-report --today
py -3 -m app.cli deliver --latest --dry-run
```

生成文件位于：

- `data/reports/beautyintel_brief_YYYY-MM-DD.md`
- `data/reports/beautyintel_brief_YYYY-MM-DD.html`

## 推送渠道

所有推送服务都支持 `dry_run`。未配置环境变量时返回 `skipped`，不会中断报告生成。

```bash
py -3 -m app.cli deliver --latest --dry-run
```

## API

启动：

```bash
make run-api
```

常用接口：

- `GET /health`
- `GET /sources`
- `POST /sources/reload`
- `GET /items?category=regulation`
- `POST /jobs/ingest?dry_run=true`
- `POST /jobs/generate-report`
- `GET /reports/latest`

## 定时任务

MVP 使用 APScheduler。默认配置项：

- `INGEST_CRON=30 7 * * *`
- `PROCESS_CRON=0 8 * * *`
- `DELIVER_CRON=30 8 * * *`

本地运行：

```bash
py -3 -m app.cli run-scheduler
```

生产环境建议迁移到 Celery Beat、Airflow、Prefect、云函数或企业内部调度系统。

## 合规注意事项

- 不绕过登录、验证码、反爬、付费墙。
- 社媒平台优先官方 API、合规第三方数据接口、人工导入 CSV/JSON。
- 所有新闻保留原始 URL。
- 摘要不得编造，重要合规事项需法务或合规复核。
- 政策法规、抽检、不符合规定、禁用原料、虚假宣传、平台规则变化会提高风险和优先级。

## Roadmap

Phase 1：MVP
- 官方源、RSS、人工导入、早报生成、基础推送。

Phase 2：品牌市场部增强版
- 竞品监控看板、周报/月报、趋势词变化、品类热度趋势、达人合作风险提示。

Phase 3：数据智能版
- 向量检索、语义去重、自动主题聚类、长期趋势数据库、多品牌/多市场配置、自动生成 campaign 灵感。

Phase 4：企业集成版
- 企业微信/飞书审批、BI 看板、权限管理、多团队订阅、合规复核流、与 CRM、CDP、电商数据打通。
