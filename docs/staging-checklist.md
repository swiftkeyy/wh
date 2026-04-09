# Staging Checklist

## Before first live Telegram payment

1. Rotate all exposed provider keys and bot tokens.
2. Confirm `PUBLIC_BASE_URL` uses valid HTTPS and is reachable from Telegram.
3. Set `AUTO_SET_WEBHOOK=true` only in staging/prod.
4. Run `alembic upgrade head`.
5. Create and verify S3 bucket access.
6. Verify `/health/ready` returns `ready`.
7. Confirm Telegram bot has payments enabled.
8. Verify Telegram Stars invoice works on a staging bot account.
9. Check successful payment updates `purchases`, `payments`, `credit_ledger`, and `subscriptions` where applicable.
10. Confirm failed jobs trigger refund path.
11. Confirm `admin_audit` shows purchases, ledger, and failed jobs.
12. Manually test `/account`, `/balance`, `/pricing`, `/purchases`, `/history`.

## First live payment end-to-end

1. Open bot in Telegram.
2. Trigger package or subscription purchase from pricing screen.
3. Complete Telegram Stars payment.
4. Verify success message in chat.
5. Verify credits or subscription state changed in database and admin audit.
6. Execute one paid generation and confirm reserve -> commit behavior.
7. Open `/health/alerts` and confirm there are no `missing_ledger_grant` anomalies.
8. Run `/admin_audit` and confirm purchase, ledger and failed jobs/alerts are coherent.

## Exit criteria

- Payment succeeds without manual DB intervention.
- Ledger remains consistent.
- User sees updated balance immediately.
- Admin can trace purchase, ledger entries, and job consumption in one flow.
- Analytics logs include `purchase_intent_created`, `stars_invoice_sent`, `payment_succeeded` or `subscription_activated`.
