# User funnel analytics — staging integration checklist

This is a **staging-only** feature. Do not merge or enable before the current app.py handlers and production storage are inspected.

## Events
- `promo_click`: recorded by a dedicated first-party redirect endpoint, not by a bare `t.me` link. Count unique random visitor identifiers; no IP tracking.
- `bot_start`: record on the actual Telegram /start handler, using Telegram user ID as actor_id.
- `registration_complete`: record only after successful committed registration.
- `first_rph_success`: record only after successful RPH delivery, never on generation attempt.

## Attribution
Telegram deep links can carry a short campaign token, e.g. `?start=fb_post`, but opening the Telegram link does not itself notify the bot. An anonymous redirect click cannot be reliably joined to a Telegram user without a signed per-visitor token and explicit handler logic. Display click counts and START counts separately; do not call their ratio a verified user conversion rate unless attribution is implemented.

## Production blockers
1. Inspect live `app.py` and locate /start, registration, document-send success and admin statistics handlers.
2. Replace temporary `/tmp` SQLite with the existing durable database (Render ephemeral disk is not durable).
3. Implement event storage with a unique constraint and safe upsert; do not modify or reset existing user/payment tables.
4. Gate admin reports behind existing admin authorization.
5. Keep analytics failures nonfatal: never block START, registration, payment or RPH delivery.
6. Verify bot handlers do not double-count retries and that registration and RPH success are real committed outcomes.
7. Test in staging, review migrations, then merge with explicit verification.

## Tests
`python -m unittest tests/test_user_funnel_analytics.py`

Do not claim these tests have run unless a runner reports success.
