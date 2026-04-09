# LumiaFlow Product Blueprint

## Product Thesis

LumiaFlow is a Telegram-first AI image product designed for repeated commercial use, not one-off novelty generation.

Core thesis:

- first value within 60 seconds,
- high-frequency reusable modes,
- credits plus subscription monetization,
- queue-safe production architecture,
- provider abstraction to protect margin and vendor risk.

## Strategic Wedges

1. B2C wow modes for acquisition: poster, action figure, manga style.
2. Utility modes for retention: photo enhance, transparent background, background replace.
3. SMB monetization wedge: product photo, social creative packs, catalog-ready outputs.

## Architecture Principles

- Telegram remains the primary interface; web admin and internal APIs stay secondary.
- FastAPI is the system edge for webhooks, callbacks, metrics, and internal operations.
- Celery handles long-running image tasks and billing/notification side workloads.
- PostgreSQL remains source of truth for money, users, jobs, and analytics facts.
- Redis is used for queue broker, caching, rate limits, and short-lived state.
- S3-compatible storage is the single binary asset layer.
- Prompt templates are versioned business assets, not hardcoded strings.

## Launch Modes

- Photo Enhance
- Background Replace
- Transparent Background
- Outfit Swap
- Product Photo
- Movie Poster
- Action Figure
- Manga Style

## Monetization Guardrails

- Free credits only for activation and referral growth, never for unlimited browsing.
- Premium modes consume more credits and are bundled into subscription tiers.
- Failed provider jobs trigger automatic refund rules based on terminal failure reason.
- Concurrency caps are applied harder to free users than paid cohorts.

## Data Priorities

- Every generation must be attributable to acquisition channel, template, provider, and margin class.
- Ledger is immutable and idempotent.
- Support and admin actions are auditable from day one.
