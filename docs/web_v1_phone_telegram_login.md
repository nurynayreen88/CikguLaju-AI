# Web V1: Telegram sign-in on desktop using a phone

Status: design only; NOT activated on public preview.

## Supported initial flow

1. Teacher opens CikguLaju Web on desktop and chooses **Log masuk dengan Telegram**.
2. Use Telegram's official website login integration on an HTTPS origin registered with the bot, following Telegram's current documentation. A teacher may complete the Telegram authorization on their phone without installing Telegram Desktop.
3. Backend validates the Telegram-signed identity (algorithm specific to the selected official login integration), checks freshness and origin/redirect protections, and issues an HttpOnly, Secure, SameSite=Lax session cookie.
4. Backend looks up the existing account by signed Telegram numeric user ID using a strictly read-only adapter; no automatic account creation or credits changes.
5. Only after successful lookup, display Rakan Pembangun/VIP/free entitlements from trusted server data. Fail closed for unknown or unlinked accounts.

## QR is a separate feature, not implied by Telegram Login Widget

Do not display a fabricated QR or use a QR containing a bearer session token. The existing `web_v1_telegram_login.py` verifies **Telegram Login Widget** payloads, not Telegram WebApp initData or a generic QR scan.

A custom QR phone-to-desktop pairing flow would require:
- a short-lived, single-use opaque pairing challenge stored server-side;
- the phone to open the official CikguLaju bot via a deep link and authenticate using the Telegram bot's trusted update `from.id`, not arbitrary URL parameters;
- a server-side atomic challenge consumption tied to the signed-in phone account;
- desktop polling authenticated to its own browser challenge, then secure cookie issuance;
- expiry, rate limits, CSRF/origin protection, replay prevention and safe logging;
- a persistent shared backend for challenge state (not in-memory Gunicorn workers).

Until all prerequisites are met, keep QR and sign-in controls disabled and label them as in development. Never request the teacher's Telegram password or one-time code in CikguLaju Web.

## Isolation

- Never read production bot token into the public preview.
- Never point staging at production database or mutate account/credits records without explicit approval.
- No production `main` branch, Render bot service or DB changes.
- Do not claim desktop-to-phone QR pairing is live based only on UI or a successful Render deployment.
