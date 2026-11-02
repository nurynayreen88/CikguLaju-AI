# CikguLaju Web ↔ Telegram: production activation checklist

**Status:** PREPARATION ONLY. This document does not authorize deployment or imply live availability.

## Current deployment
- Telegram Render service: `srv-dah3b8lbedkc738ugqt0`; branch `main`; start `gunicorn app:app`; auto-deploy enabled.
- Web staging API: `srv-dbjcpsk9v7es739o39a0`; branch `staging/cikgulaju-web-v1`; start `gunicorn --bind 0.0.0.0:$PORT tools.run_web_v1_preview:app`; auto-deploy disabled.
- Telegram authoritative master must be confirmed as v26.00 **in the running process**. Do not substitute staging SQLite snapshots.

## Prerequisites (do not skip)
1. Review the staging diff and obtain approval for a narrowly scoped production PR; do not merge the whole staging branch into `main`.
2. Confirm existing Telegram bot webhook, database persistence, and account/payment flows work before changes.
3. Produce a dedicated randomly generated API token (>=32 characters), stored as a Render secret on BOTH services. Never commit or print the token.
4. In the Telegram service, set `CIKGULAJU_CURRICULUM_API_ENABLED=1` and `CIKGULAJU_AUTHORITATIVE_API_TOKEN` only after the reviewed API code is present. Do not change `BOT_TOKEN`, `WEBHOOK_URL`, or the database volume.
5. The optional entrypoint `tools.run_telegram_with_curriculum_api:app` is NOT active with the current `gunicorn app:app` command. A production start-command change requires a reviewed, scheduled deployment and rollback readiness. The isolated staging entrypoint `tools.run_telegram_curriculum_wsgi:app` MUST NEVER be used for Telegram production.
6. In Web API staging, set `CIKGULAJU_AUTHORITATIVE_API_URL=https://cikgulaju-ai.onrender.com` and the SAME dedicated token. Deploy the staging service explicitly after tests pass. Do not configure a copied SQLite database as a substitute.

## Acceptance checks
- Without token: `GET /internal/curriculum/v1/subjects?year=2` -> HTTP 401 when enabled.
- With token: response HTTP 200, `source=telegram-runtime-v1`, and verified `items` from active v26.00 database.
- Confirm `Cache-Control: no-store` and `Vary: Authorization`.
- Verify Year 2 -> English -> Unit -> Lesson in Web using an authenticated existing Telegram account.
- Confirm the Telegram webhook, RPH generation, user status and payment approval remain unaffected.
- `approved-materials` currently returns HTTP 503 intentionally; downloads are NOT ready until approved mappings and delivery authorization are implemented.

## Rollback
- Revert Telegram start command to `gunicorn app:app` and disable `CIKGULAJU_CURRICULUM_API_ENABLED`; redeploy last known good production commit.
- Restore Web API staging to its last known good deploy if needed. Web must fail closed rather than fall back to a different database.
- Do not reset, overwrite, migrate, or recreate the Telegram master DB as part of rollback.

## Known unresolved blocker
Web HTTP 503 (`TELEGRAM_CURRICULUM_API_NOT_CONNECTED`) persists until a reviewed Telegram runtime endpoint is actually enabled and Web URL/token are configured. Passing CI is not evidence of a live connection.
