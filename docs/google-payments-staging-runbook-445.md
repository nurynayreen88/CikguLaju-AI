# Google Login + Web Receipt Staging — Deployment and Acceptance Runbook

**Status (7 Nov 2026):** Draft PR #447 has a dedicated, isolated Render staging service that has deployed successfully. **Google login remains DISABLED intentionally.** There is not yet a separate CikguLaju Supabase staging project or provider credentials. Live CikguLaju production and its user records remain untouched. No real payment is authorized.

- Staging service: https://cikgulaju-google-payments-staging.onrender.com
- Render service ID: `srv-dbn8hrm417fc73dr5itg`; current branch: `feature/web-google-auth-staging-445`; auto-deploy OFF.
- `/healthz` reports process liveness, not Google login readiness.
- `/readyz` responds 503 while the isolated OAuth/admin settings are not configured. A successful Render deploy does **not** mean that signing in with Google works.
- `/google-staging-login` displays a non-interactive, clear Malay maintenance page (HTTP 503) when the safe Google feature gate is closed, rather than inviting the user to a broken OAuth flow.
- Connected Supabase account was checked: CikguLaju production is the only active CikguLaju database project; no separate staging project was found. Do not reuse or rename another app's Supabase project for this purpose.

## Isolation
Provision a **separate** Supabase staging project, in a user-confirmed organization after any cost approval. Do not reuse production CikguLaju (known only by the existing deployment configuration). Never point testing at `SUPABASE_URL` from Telegram production or the Web production service.

The separate Render *Web Service* already exists. Keep it distinct from `cikgulaju-web` production:
- Repository: `nurynayreen88/CikguLaju-AI`
- Branch: `feature/web-google-auth-staging-445`
- Build: `pip install 'Flask==3.1.3' 'gunicorn==23.0.0'`
- Start: `gunicorn --bind 0.0.0.0:$PORT tools.run_google_payments_staging:app`
- Auto-deploy: disabled until manual QA
- Tests: `.github/workflows/google-web-auth-staging.yml` (Python + disposable PostgreSQL 17)
- No Telegram production runtime or user-facing RPH generator is imported

## Create isolated staging schema

Execute **only on staging** (in this order):
1. `migrations/STAGING_ONLY_web_google_identity_445.sql`
2. `migrations/STAGING_ONLY_web_google_payments_445.sql`
3. `migrations/STAGING_ONLY_web_private_receipt_bucket_445.sql`
4. `migrations/STAGING_ONLY_web_payment_review_rpc_445.sql`

Review SQL and RLS with Supabase advisors first, then verify `web-receipts-staging` is private and has a 4 MB limit. Only the backend service-role key may access these tables or receipts; never expose that key in browser code.

## Supabase Auth / Google Cloud setup

In the **staging project only**, configure the Google provider. In Google Cloud create/configure the OAuth web client with the staging Supabase Auth callback:

`https://<STAGING_SUPABASE_REF>.supabase.co/auth/v1/callback`

Put Google's OAuth client ID/secret into the **staging Supabase Auth provider settings**, not Render source code or a chat. Add the exact staging Web callback to Supabase Auth allowed redirect URLs:

`https://<STAGING_RENDER_HOST>/api/auth/google/callback`

This project uses PKCE and the server-side `/auth/v1/user` response to verify the user. Google email, user metadata, or Telegram username are never used to merge existing accounts.

## Dedicated staging Telegram bot for administrators

Create/configure a **staging admin bot**, separate from the live CikguLaju bot. Configure its allowed login domain as the staging Web host; use Telegram's Login Widget to sign in at `/admin/google-staging-login`. Admin Telegram user IDs must be explicitly allowlisted in the environment. Reuse the staging bot for optional admin receipt notifications, not the teachers' Telegram chats.

## Staging environment variables (secrets only in Render)

Required:
- `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED=1`
- `CIKGULAJU_GOOGLE_STAGING_PROJECT_REF=<staging-project-ref>`
- `CIKGULAJU_GOOGLE_PRODUCTION_PROJECT_REF=<production-project-ref>` (denylist; no production credentials required)
- `CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL=https://<staging-project-ref>.supabase.co`
- `CIKGULAJU_GOOGLE_STAGING_SUPABASE_PUBLISHABLE_KEY=<staging-publishable-key>`
- `CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY=<staging-secret-backend-key>`
- `CIKGULAJU_WEB_SESSION_SECRET=<independent-random-secret-at-least-32-chars>`
- `CIKGULAJU_GOOGLE_STAGING_ORIGIN=https://<staging-render-host>`
- `CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST=<staging-render-host>`
- `CIKGULAJU_GOOGLE_STAGING_ADMIN_TELEGRAM_IDS=<allowed-telegram-admin-id-list>`
- `CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_TOKEN=<dedicated-staging-bot-token>`
- `CIKGULAJU_GOOGLE_STAGING_ADMIN_BOT_USERNAME=<dedicated-staging-bot-username>`
- `CIKGULAJU_GOOGLE_STAGING_PAYMENT_CATALOG_JSON=<explicit-server-approved-test-plan-config>`

Optional:
- `CIKGULAJU_GOOGLE_STAGING_ADMIN_CHAT_ID` (for receipt notifications)
- **Do not configure a real TNG payment URL in staging**. Public staging API always returns an empty payment link and `test_mode=true`.

Avoid importing `SUPABASE_SECRET_KEY`, live Telegram bot tokens, or CikguLaju production payment credentials into the staging Render service.

## Acceptance test

1. Open `https://<staging-render-host>/google-staging-login`; sign in with a new Google identity without Telegram.
2. Verify account is created once (UUID mapping), subsequent login reuses account, initial `google_trial_remaining=10`.
3. On `/google-staging-payments`, submit a **test-only** PDF/image receipt. Do NOT transfer money. Confirm one pending request, 4 MB cap, private Storage object, no second pending duplicate.
4. Verify an admin notification via the dedicated staging Telegram bot, where configured; failures must not discard the pending record.
5. Open the secured link. If not logged in, admin goes to `/admin/google-staging-login` and authenticates via verified widget; selecting a teacher displays receipt and approval/rejection fields.
6. Reject with a reason; verify teacher sees rejection and can submit a fresh corrected receipt. Existing rejected request remains immutable.
7. Approve a fresh request; confirm **exactly one** entitlement. Replay action, confirm no duplicate, and verify status on the Google Web account page.
8. Test expired or forged Google/admin cookies, wrong origin, non-allowlisted Telegram account, mismatched Supabase project ref, legacy production endpoints (must 404), and real TNG links (must never render).
9. Verify both Python and PostgreSQL CI jobs pass.
10. On any unexpected result: disable `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED`, leave the existing CikguLaju production services and database unchanged.

## Not yet authorized for production

Do **not** launch real checkout, collect money, or merge this draft PR while these remain unresolved:
- Shared canonical user identity migration and independently verified Google–Telegram linking.
- Google-only RPH generation and atomic debit of the same 10-trial-credit rules.
- Shared account-bound profile, referral, payments and subscriptions across Telegram and Web.
- Single global cap for the first 200 Rakan Pembangun slots across both login methods.
- Production approved prices and plans, payment reconciliation and admin rollout.
- Real-device Google OAuth/browser test with an actual staged Supabase Auth provider.

This runbook describes steps; it is not a claim that staging or production deployment has occurred.


## Pending requirements to enable login — owner-managed external credentials
- Create a **new, isolated Supabase staging project** only after checking organization billing/eligibility. Do not activate migration SQL on the active production CikguLaju database.
- At Google Cloud Console → Google Auth Platform → Clients, create a **Web application** OAuth client. Set authorized origin to `https://cikgulaju-google-payments-staging.onrender.com`. Add Google redirect URI **`https://<NEW_STAGING_REF>.supabase.co/auth/v1/callback`**, using the exact value displayed by Supabase Auth.
- In new Supabase staging project → Authentication → Providers → Google, enable the provider and enter the Google client ID and **secret privately in the dashboard**.
- Supabase Auth redirect URL allow list must contain `https://cikgulaju-google-payments-staging.onrender.com/api/auth/google/callback`; do not put the Web callback into Google's redirect-URI field.
- In Render staging service environment, add only the staging ref/URL/publishable key/server secret and app session secret listed above, plus the known *different* production project ref for the runtime denylist. Use private environment settings; never place credentials into a chat, GitHub issue, commit or URL query.
- Apply the four staged SQL files to the newly created staging project in the prescribed order, review security policies/RLS, then enable `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED=1` and manually redeploy **staging only**.
- Run an actual Google OAuth login with a fresh Google account; confirm new UUID account with 10 trial credits, repeat login idempotence, and that no Telegram user or existing paid entitlement is modified.
- Until production-ready canonical linking and atomic RPH quota integration pass tests, **Google login must not grant access to the existing live RPH dashboard**. Do not automatically merge users by matching emails, display names or Telegram usernames.

Docs checked for Google/Supabase hosted redirects: https://supabase.com/docs/guides/auth/social-sign-in/auth-google and https://supabase.com/docs/guides/auth/redirect-urls
