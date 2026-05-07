# BeautyIntel Brief cloud deployment

This project can run as a normal web service. Once deployed, other people can open:

```text
https://YOUR-SERVICE-URL/reports/latest/view
```

The server must keep running. Your local computer does not need to stay on.

## Recommended option: Render

1. Create a GitHub repository and upload this project.
2. Open Render: https://render.com
3. Choose **New > Blueprint**.
4. Connect the GitHub repository.
5. Render will read `render.yaml`.
6. Deploy the service.

The included `render.yaml` creates:

- A Docker web service
- A persistent disk mounted at `/app/data`
- SQLite database at `/app/data/beautyintel.db`
- Background daily refresh enabled
- Default schedule: `30 8 * * *` in `Asia/Shanghai`

## Important URLs

After deployment, replace `YOUR-SERVICE-URL` with the Render URL.

```text
https://YOUR-SERVICE-URL/health
https://YOUR-SERVICE-URL/reports/latest/view
https://YOUR-SERVICE-URL/reports/refresh-today
```

## Environment variables

Required:

```env
DATABASE_URL=sqlite:////app/data/beautyintel.db
BRIEF_TIMEZONE=Asia/Shanghai
ENABLE_BACKGROUND_SCHEDULER=true
DELIVER_CRON=30 8 * * *
```

Optional delivery variables:

```env
LARK_WEBHOOK_URL=
SLACK_WEBHOOK_URL=
GENERIC_WEBHOOK_URL=
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=
EMAIL_FROM=
EMAIL_TO=
```

## Manual refresh

Open this URL in a browser:

```text
https://YOUR-SERVICE-URL/reports/refresh-today
```

It will fetch sources and regenerate today's report.

## Local Docker test

```bash
docker build -t beautyintel-brief .
docker run --rm -p 8001:8001 -e ENABLE_BACKGROUND_SCHEDULER=false beautyintel-brief
```

Then open:

```text
http://127.0.0.1:8001/reports/latest/view
```
