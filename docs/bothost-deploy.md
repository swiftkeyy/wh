# Bothost Deploy Guide

## Recommended deployment model

For this project, deploy it as separate services:

1. `api` service
2. `worker` service
3. managed PostgreSQL
4. managed Redis
5. external S3-compatible object storage

This is better than forcing the whole product into one process, because image jobs and billing reliability depend on a background worker.

## Why Bothost is a good fit

Based on Bothost public pages, they support:

- aiogram 3.x and Python bots
- SSL webhook URLs
- Git-based deploys
- Docker containers
- PostgreSQL and Redis on paid tiers

Sources:

- [Bothost Telegram bots](https://bothost.ru/telegram-bots)
- [Bothost main site](https://bothost.ru/)

## Service 1: API

Build/install command:

```bash
pip install .
```

Start command:

```bash
python -m app.run_api
```

## Service 2: Worker

Build/install command:

```bash
pip install .
```

Start command:

```bash
python -m app.run_worker
```

## One-time migration job

Run once after deploy:

```bash
python -m app.run_migrate
```

## Environment variables

Required:

- `APP_ENV=production`
- `APP_NAME=WHYNOT Photoshop`
- `PUBLIC_BASE_URL=https://<bothost-public-url>`
- `AUTO_SET_WEBHOOK=true`
- `TELEGRAM_BOT_TOKEN=...`
- `TELEGRAM_WEBHOOK_SECRET=...`
- `POSTGRES_DSN=postgresql+asyncpg://...`
- `REDIS_URL=redis://...`
- `S3_ENDPOINT_URL=...`
- `S3_ACCESS_KEY=...`
- `S3_SECRET_KEY=...`
- `S3_BUCKET=...`
- `S3_REGION=...`
- `REMOVE_BG_API_KEY=...`
- `GOOGLE_GENAI_API_KEY=...`
- `JOB_PRICING_JSON=...`
- `PURCHASE_PACKS_JSON=...`
- `SUBSCRIPTION_PLANS_JSON=...`
- `ADMIN_TELEGRAM_IDS=...`

## Deploy order

1. Create PostgreSQL and Redis.
2. Configure S3-compatible bucket.
3. Deploy `api`.
4. Run migrations.
5. Deploy `worker`.
6. Check `/health/ready`.
7. Verify `/health/alerts`.
8. Trigger webhook registration.
9. Test `/start`, `/pricing`, `/account`.
10. Run first manual Stars payment.

## Recommendation

If Bothost account supports multiple services and managed PostgreSQL/Redis, use it.
If your current Bothost plan only supports a single lightweight bot process, this project is too serious for that plan and should not be squeezed into it.
