# Google–Telegram paid status bridge: staging release gate (2026-11-07)

**State:** Code prepared and testable on branch `feature/web-google-auth-staging-445`. Staging can show paid status only AFTER a separately approved production Web rollout. It currently runs safely with both bridge feature flags off. No production deployment is authorised by this document.

## Authoritative records

The existing CikguLaju Telegram **production** Supabase project, and not the Google staging project, is the source of truth.

- `cikgulaju_users.telegram_user_id` identifies the pre-existing user.
- `pioneer_entitlements` with `entitlement='PIONEER_LIFETIME'` and `revoked_at IS NULL` identifies verified lifetime Rakan Pembangun access.
- `subscriptions` with `status='active'` and `expires_at > now()` identifies active time-limited subscription.
- Never infer payment approval from `bot_payment_requests`, a submitted receipt, or browser claims.
- A production account missing from the source must NOT be auto-created.
- Trial credits in the production database and `web_accounts.google_trial_remaining` in staging are currently **different ledgers**.

## Two-stage release, separate approvals required

**1. Production Web API rollout (NOT DONE).** Review and deploy `web/telegram_prod_paid_status_bridge.py` registered by `tools/run_web_production.py` only in the existing production Web service. Maintain all existing Telegram bot, payment, and RPH routes. Ensure `SUPABASE_URL` is the verified production project and `SUPABASE_SECRET_KEY` is available only on the production server. Set `CIKGULAJU_PAID_BRIDGE_PRODUCTION_ENABLED=1` and one new **dedicated** secret `CIKGULAJU_PAID_BRIDGE_TOKEN` (at least 48 characters) in production Web Render private environment. DO NOT print or commit it. The API is POST-only `/internal/identity/v1/entitlements`, exact host `cikgulaju-web.onrender.com`, private token required, no redirects or public account browsing. Verify invalid/missing token 401, wrong host 403, missing legacy user 404, and exact private payload 200 only under the server-to-server token. No production write.

**2. Staging read activation (NOT DONE).** Configure the **same** dedicated bridge token in isolated staging Render and set `CIKGULAJU_PAID_BRIDGE_STAGING_READ_ENABLED=1`. Deploy staging after production API has passed token, host, and trusted-record checks. A staging account must already be linked to the exact Telegram identity using the Widget signature and the checked database mapping. No browser ID is accepted. The endpoint `GET /api/google-staging/web/access/status` should show a `production_access_status` of `verified`, `not_linked`, `production_account_missing`, or `source_unavailable`. A disabled bridge reports `bridge_disabled`; it MUST NOT report a false inactive subscription.

## Current deliberate non-goals

- No production payment approval, trial-credit mutation, receipt migration, referral reconciliation, or entitlement copy.
- No production access grant or skipped RPH debit based merely on the private status-read result. The staging RPH generator has its own atomic one-bundle/one-credit ledger; paid production access must not be treated as staging credit exemption without a separate reviewed paid-access transaction policy.
- No production bot service change; only a proposed opt-in API on the production **Web** service.
- No production deployment or merge while the release gate is pending.
- On outage, timeout, wrong token, mismatched identity, revocation, or malformed response: fail closed and show `source_unavailable`, never fall back to a paid grant.

## Verification checklist

1. Run `test_private_production_paid_status_bridge.py`, `test_staging_production_paid_status_client.py`, and existing linked Google–Telegram auth and RPH tests.
2. Confirm the production lookup is authenticated and returns only booleans, optional expiry, and matching legacy Telegram ID. Names, receipts, references, credits and email must not be included.
3. Prove two linked login methods return the SAME snapshot and an unlinked Google account cannot query any Telegram record.
4. Revoke a test lifetime entitlement in an isolated fixture and prove the next lookup returns inactive. Do not revoke any real user's production access for this test.
5. Prove retry, offline production, and stale/expired subscription never grant staging paid access or spend additional credits.
6. Validate 3/3 staging CI, then obtain explicit owner approval for the production API rollout **before** altering production services.

## Existing verified status

On 2026-11-07 a single staging-linked legacy Telegram user was verified with **active, non-revoked Rakan Pembangun lifetime** in production via admin-authorized *read-only* Supabase query. The production status is NOT automatically reflected in staging until both endpoint and staging client are enabled.
