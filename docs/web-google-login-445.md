# Web Google Login — Issue #445

Status: implementation design on isolated branch; **not live**.

## Required user experience
- Primary: Continue with Google. Secondary: Login with Telegram.
- Google users can register and access Web without installing Telegram.
- Profile completion happens after successful sign-in.
- Preserve Telegram login and all existing users.

## Identity and migration contract
- Additive provider identities table: internal_user_id (FK), provider ('google'/'telegram'), provider_subject, created_at, UNIQUE(provider,provider_subject).
- Preserve existing internal user IDs and entitlements. Never use email alone to merge accounts.
- Verify Google OIDC ID token on backend: issuer, audience, signature, expiry, nonce; validate OAuth state and PKCE.
- Link providers only after reauthentication of both identities, with audit log and unique constraint.
- Existing quotas, Rakan Pembangun, payments and subscriptions remain keyed to canonical internal user ID.
- No duplicate free trials when providers are linked. Existing users do not receive fresh quota.
- Keep Telegram admin notifications; optional end-user Telegram notifications only when linked.

## Configuration
- GOOGLE_OAUTH_CLIENT_ID and GOOGLE_OAUTH_CLIENT_SECRET (secret in Render env, never git)
- GOOGLE_OAUTH_REDIRECT_URI = https://cikgulaju-web.onrender.com/auth/google/callback (verify actual route in code before registering)
- HTTPS-only secure session cookie; HttpOnly, SameSite=Lax; protect against CSRF and session fixation.

## Rollout checklist
1. Locate Web Flask authentication entry points and actual user model.
2. Back up database; inventory Telegram identity, quota and entitlement relationships.
3. Implement additive migration and OAuth routes; do not silently replace Telegram auth.
4. Build Google-first sign-in UI; show helpful error and fallback on failed login.
5. Tests: new Google user, existing Telegram user, provider linking, collision and duplicate prevention, quotas, payments, admin access, logout, mobile browsers.
6. Deploy to staging only; verify callback URI, secrets, migrations and rollback.
7. Require explicit approval before production deployment.

**No production configuration or database changes are authorized by this file.**

## Confirmed integration findings (2026-11-07)
- Render production Web service uses branch `production/cikgulaju-web-20261105` and entrypoint `tools.run_web_production:app`; Telegram service deploys from `main` separately. This feature branch does not auto-deploy either service.
- `web_v1_telegram_auth_routes.py` issues a signed session ticket with Telegram numeric UID and `cikgulaju_web_v1_session` cookie; `_lookup` checks Supabase accounts keyed by Telegram UID. `tools/run_web_v1_preview.py` and other routes directly compare `account.telegram_user_id == uid`.
- `web/web_payment_routes.py` also relies on the Telegram UID for account membership and the Telegram bot's payment queue. **Adding Google OAuth alone will not grant functional Web access.**
- First introduce a canonical internal identity resolver and a provider mapping (Google sub / Telegram UID) across session checks, catalogue, RPH, profile, payment, referral, and quotas. Preserve Telegram UID where legacy Telegram operations require it; never fabricate a Telegram ID for Google users.
- For Google-only users, explicitly adapt payment and admin flows to canonical internal IDs, or block those flows with a clear explanation until safe. No anonymous payments or unverified entitlements.
- Existing `_config()` currently requires Telegram bot credentials, so separate provider-independent Web session configuration from Telegram widget configuration without weakening existing validation.
- Google OAuth callback and secrets cannot be finalized until Google Cloud OAuth client is configured for the actual staging/production domains.
- Before coding migration, inspect Supabase tables and RLS; use additive, reversible schema and do not modify production data.

## Live Supabase read-only schema inventory
Project: CikguLaju (ap-southeast-1). The public `cikgulaju_users` table uses `telegram_user_id bigint` and stores `trial_remaining` and `credits`. `teacher_profiles` also uses `telegram_user_id bigint`; `payments`, `subscription_payments`, and `pioneer_payment_requests` refer to Telegram IDs. This confirms that the proposed identity mapping alone is insufficient unless all account-bound routes are migrated.

Suggested safe staged schema design (NOT applied): new `web_accounts` with UUID primary key, new `web_account_identities` with provider+subject unique constraint, and a nullable Telegram legacy ID mapped one-to-one to existing `cikgulaju_users`. New Google users get UUID accounts and independent trial counters; existing Telegram accounts are mapped lazily or backfilled transactionally. New payment/profile records must use UUID references, with legacy Telegram bridge retained. Never use fabricated Telegram IDs, or write new Google users into legacy tables requiring a Telegram UID. Confirm existing RLS and constraints before any DDL.

Important: Supabase Auth's built-in Google identity linking can automatically link by verified email; that is not equivalent to proving ownership of an existing Telegram account. Require separate explicit verified Telegram linking for legacy accounts.
