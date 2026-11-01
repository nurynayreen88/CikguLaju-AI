# Web V1 Telegram Login — staging deployment checklist

The isolated Flask API now mounts `POST /api/auth/telegram/widget`,
`GET /api/auth/telegram/session`, and `POST /api/auth/telegram/logout`.

## Fail-closed default
All login requests return HTTP 503 unless the isolated **web** Render service
has explicit credentials and a verified read-only SQLite account mapping.
Do not configure this on the production Telegram Render service.

## Required isolated web environment
- `CIKGULAJU_WEB_BOT_TOKEN`: server-side Telegram bot token; never expose to JS.
- `CIKGULAJU_WEB_SESSION_SECRET`: independent random secret, >=32 characters.
- `CIKGULAJU_WEB_ACCOUNT_DB`: actual readable, explicitly approved SQLite DB path.
- `CIKGULAJU_WEB_ACCOUNT_TABLE`
- `CIKGULAJU_WEB_ACCOUNT_ID_COLUMN`
- `CIKGULAJU_WEB_ACCOUNT_LIFETIME_COLUMN`
- `CIKGULAJU_WEB_ACCOUNT_CREDITS_COLUMN`
- Optional: `CIKGULAJU_WEB_ACCOUNT_VIP_COLUMN`.

No schema inference, DB copy, or production DB modifications are permitted.
The database adapter opens SQLite with `mode=ro`. SQLite file must be mounted
or otherwise safely accessible; the existing production database is not
automatically shared between Render services.

## Before enabling the frontend
1. Confirm exact account schema on an authorized database copy.
2. Configure official Telegram Login Widget domain with BotFather.
3. Verify the widget payload against a real Telegram account in staging.
4. Implement a CSRF-resistant widget frontend flow and wire account status.
5. Verify cookie/session behavior over HTTPS and revoke access on entitlement changes.
6. Test RPH generation and credits with a separate authorized backend integration.

**Not ready for public launch.** The existing bot and production DB are untouched.
