# Google Login + Web Receipt Staging — Deployment and Acceptance Runbook

**Status (7 Nov 2026):** Draft PR #447 has a dedicated, isolated Render staging service that has deployed successfully. **Google login remains DISABLED intentionally.** A separate CikguLaju Supabase staging project is now ACTIVE and its four isolated migrations are applied; Google provider credentials are not yet configured. Live CikguLaju production and its user records remain untouched. No real payment is authorized.

- Staging service: https://cikgulaju-google-payments-staging.onrender.com
- Render service ID: `srv-dbn8hrm417fc73dr5itg`; current branch: `feature/web-google-auth-staging-445`; auto-deploy OFF.
- `/healthz` reports process liveness, not Google login readiness.
- `/readyz` responds 503 while the isolated OAuth/admin settings are not configured. A successful Render deploy does **not** mean that signing in with Google works.
- `/google-staging-login` displays a non-interactive, clear Malay maintenance page (HTTP 503) when the safe Google feature gate is closed, rather than inviting the user to a broken OAuth flow.
- Connected Supabase account was checked: a dedicated project `CikguLaju-Google-Staging` has been created in organization `ContentLajuAI`, region `ap-southeast-1`, project ref `eqrcjlnvcytkgazptbor`, reported cost $0/month by Supabase. Original production project remains `soxakntcanbycjoygrcx` and was not modified.
- All four staging-only SQL migrations successfully applied to project `eqrcjlnvcytkgazptbor`, with staging bucket `web-receipts-staging` private, 4 MiB cap. Security audit confirms RLS on all four new tables and `anon`/`authenticated` roles have no SELECT access; `service_role` has SELECT. A migration-time advisor `rls_enabled_no_policy` INFO finding is deliberate in this server-only model, **do not add permissive public policies**.
- Staging SQL QA: two calls to `ensure_google_web_account` for the same synthetic Google UUID resolved to one account with initial 10 trial credits; temporary test rows deleted.
- Render staging environment now contains staging URL/ref, verified distinct production-ref denylist, publishable key, exact origin/host, independent cryptographically generated session secret, and `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED=0`. No staging service-role key or Google OAuth client credentials configured yet.

## Isolation
The **separate** Supabase staging project has now been created with explicit user organization approval and $0/month quoted cost; its schema has been provisioned. Do not reuse production CikguLaju (known only by the existing deployment configuration). Never point testing at `SUPABASE_URL` from Telegram production or the Web production service.

The separate Render *Web Service* already exists. Keep it distinct from `cikgulaju-web` production:
- Repository: `nurynayreen88/CikguLaju-AI`
- Branch: `feature/web-google-auth-staging-445`
- Build: `pip install 'Flask==3.1.3' 'gunicorn==23.0.0'`
- Start: `gunicorn --bind 0.0.0.0:$PORT tools.run_google_payments_staging:app`
- Auto-deploy: disabled until manual QA
- Tests: `.github/workflows/google-web-auth-staging.yml` (Python + disposable PostgreSQL 17)
- No Telegram production runtime or user-facing RPH generator is imported

## Google-first account screen (staging code, still OAuth-disabled)

- Verified Google browser callback redirects to `/google-staging-account` **instead of the payment page**.
- This page calls `GET /api/auth/google/profile` with the signed, HttpOnly staging Google cookie. Server-side lookup fetches `display_name` and `google_trial_remaining` only for the verified canonical UUID in `public.web_accounts`, with the private service key on the backend.
- Shows a staging-only 10-credit counter, a clearly labelled **RPH not yet available** message, a link to the test receipt page, and a same-origin POST logout action.
- Anonymous or forged identities get HTTP 401; no client-selected account_id, email, or Telegram ID is accepted. Profile responses are no-store/private.
- `tests/test_web_google_staging_profile.py` and the Google route regression suite verify the read-only, account-bound query and browser destination. This does not prove actual Google provider login works; real browser acceptance still requires Cloud OAuth setup.
- Service remains fail-closed: `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED=0` until setup completes.

## OAuth redirect mismatch found during real browser trial (7 Nov 2026)

**Observed:** After Google consent, the teacher arrived at `http://localhost:3000/?code=...`, not at the protected Render callback. This is the default **Supabase Site URL**. The staging app initiates OAuth with `redirect_to=https://cikgulaju-google-payments-staging.onrender.com/api/auth/google/callback?state=<random-hex>`. The previously documented exact allowlist path omits the dynamic query string. Supabase Auth logs corroborated `localhost:3000` as the redirect/referrer; the Web callback has not been called successfully.

**Action in staging-only Supabase dashboard** https://supabase.com/dashboard/project/eqrcjlnvcytkgazptbor/auth/url-configuration :

1. Set **Site URL** to `https://cikgulaju-google-payments-staging.onrender.com` (remove localhost default).
2. Add **Redirect URLs** entry `https://cikgulaju-google-payments-staging.onrender.com/api/auth/google/callback**` (the `**` suffix covers dynamic `?state=...`). Keep the existing exact entry if present. For production avoid broad wildcards; this is isolated to staging.
3. Save the two settings and start a **fresh** OAuth login from `/google-staging-login`. A previous `?code=` value is short-lived and single-use; don't paste it into chats or URLs.
4. Verify the browser reaches the **Render** callback and then `/google-staging-account`, showing the 10 staging trial credits. If not, inspect Auth and Render server logs before further changes.

This is an **owner dashboard configuration**, not a change to the code or production database. GitHub's no-credential provider smoke verifies that authorization starts at Google, but **cannot verify Google returns to the configured Web callback without a human sign-in**.

## Remaining blocker after staging DB provisioning (7 November 2026)

**No successful Google browser OAuth login has occurred yet.** Google Cloud OAuth web client and its client ID/secret must be configured privately in the staging Supabase project at https://supabase.com/dashboard/project/eqrcjlnvcytkgazptbor/auth/providers. Staging backend `CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY` also must be set privately in Render; the connected Supabase tool exposes only publishable API keys, not server secrets. Keep `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED=0` until all staging-only credentials and Auth redirect URLs are verified.

Once configured: run browser sign-in and account idempotence acceptance tests before considering production. Google users should **not** gain RPH access in this staging implementation.

## Create isolated staging schema

The four migrations were **applied to the new staging project** (in this order); on future fresh staging projects, execute only on staging:
1. `migrations/STAGING_ONLY_web_google_identity_445.sql`
2. `migrations/STAGING_ONLY_web_google_payments_445.sql`
3. `migrations/STAGING_ONLY_web_private_receipt_bucket_445.sql`
4. `migrations/STAGING_ONLY_web_payment_review_rpc_445.sql`

Review SQL and RLS with Supabase advisors first, then verify `web-receipts-staging` is private and has a 4 MB limit. Only the backend service-role key may access these tables or receipts; never expose that key in browser code.

## Supabase Auth / Google Cloud setup

In the **staging project only**, configure the Google provider. In Google Cloud create/configure the OAuth web client with the staging Supabase Auth callback:

`https://eqrcjlnvcytkgazptbor.supabase.co/auth/v1/callback`

Put Google's OAuth client ID/secret into the **staging Supabase Auth provider settings**, not Render source code or a chat. Add the exact staging Web callback to Supabase Auth allowed redirect URLs:

`https://cikgulaju-google-payments-staging.onrender.com/api/auth/google/callback`

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
