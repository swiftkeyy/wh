# Secrets Strategy

## Principle

Local `.env` is only for developer convenience. Staging and production must read secrets from environment injection or a secret manager.

## Recommended split

- Local dev: `.env` or `.env.local`
- Staging: CI/CD injected environment variables or container platform secrets
- Production: secret manager or orchestrator-managed secrets

## What should never be committed

- Telegram bot token
- Telegram webhook secret
- remove.bg API key
- Google GenAI API key
- database passwords
- S3 credentials
- Sentry DSN if treated as sensitive in your org

## Recommended delivery

1. Build immutable image once.
2. Inject environment-specific secrets at deploy time.
3. Keep `.env.staging.example` and `.env.prod.example` as templates only.
4. Rotate provider keys if they have ever been exposed in chat, logs, or screenshots.
