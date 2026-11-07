# CikguLaju Web — Google-first integration gates (7 Nov 2026)

## Current tested milestone

The owner completed real Google Auth browser login through Supabase staging and
landed on `/google-staging-account` with **10 staging credits**. The new
`/google-staging-web` selector is a *read-only* route protected by the same
verified Google identity. It imports existing
`web.unified_rph_web.unit_options` / `pdp_options` to list source-backed
Tahun 2–6 English, Moral, PJPK (PJ/PK), and PSV unit/PdP metadata.
No duplicate static lesson list, document generator, mock entitlement, or
production read/write backend was introduced.

At the current milestone:
- Google credentials and cookie are isolated to
  `cikgulaju-google-payments-staging.onrender.com`.
- User can browse available Year/Subject/Unit/Lesson metadata and click
  **Papar Bahan**; no RPH file is exposed, no download URL is returned.
- Google staging quota is **display-only**, not 10 productive RPH downloads.
- Telegram's existing `cikgulaju_web_v1_session` remains unchanged.
- Neither Google names nor emails are valid account-linking keys.
- All production RPH generator, Web schedules, RPT and payments are untouched.

## Real source of truth and why production merge is not yet safe

The existing Web account is keyed by Telegram numeric ID:
`web_v1_telegram_auth_routes._lookup` reads
`cikgulaju_users.trial_remaining`, pioneer entitlements, and subscriptions
from the authoritative Supabase project. Both the Web RPH entitlement gate
(`web/english_rpt_2027_http._account`) and the actual successful-file quota
debit (`web/rph_delivery_quota.authorize_rendered_document`) depend on a
verified Telegram ID. The native Telegram RPH renderer itself is used by
`web/unified_rph_web.py` and must not be substituted with generic Word/PDF.

Google staging uses a UUID identity from a **different** Supabase project.
Never pass Google UUID into Telegram's signed session format; never fabricate
Telegram IDs; never copy a paid entitlement just because display/email match.

## Next integration gates, in non-destructive order

1. **Design and test additive production identity mapping**, keeping the
   original Telegram IDs and all existing entitlements, receipts, quota rows,
   referer/referral attribution and 200 Rakan Pembangun first-batch limit.
   Before any production migration, perform a snapshot, FK/orphan/duplicate
   audit and review the change.
2. **Implement verified optional account linking**, requiring independently
   verified live Google and Telegram sessions at one browser action. The
   linking procedure must be transactionally idempotent and must not create
   a second 10-credit allowance for a linked legacy account. Never merge by
   email, display name or user-supplied IDs.
3. **Introduce UUID-aware, atomic RPH trial debit** in the *authoritative*
   account database for Google-first standalone accounts. Debit once only
   after the exact native Telegram-backed PDF/Word is successfully rendered,
   with replay-idempotency, zero-credit rejection and uncertain-commit
   handling. Paid Rakan Pembangun/VIP have no debit. No Google RPH grants
   solely from the staging `web_accounts.google_trial_remaining`.
4. **Wire native Google session verification** into the existing Web
   `_account()`/catalogue, teacher schedule/profile, RPH download,
   referral and RPT paid-access boundaries; preserve Telegram-only behavior
   for all legacy clients. Require exact hostname + secure cookie and never
   expose service-role keys to JavaScript.
5. **Payment review parity:** confirmed Google manual receipt reviewed by
   authorized admin, scoped only to canonical account, idempotent
   approval/rejection; notifications in Telegram are only admin messages,
   not a mandatory teacher login. Verify no duplicate lifetime places.
6. **Staging acceptance matrix:** new Google signup; 10 initial credits;
   one completed native RPH -> 9; failure -> 10; exhaustion -> 403; paid
   user unlimited; existing Telegram account unchanged; explicit dual-login
   linking; no linking by name/email; receipt and admin approval; referral;
   browser session/logout/replay/CSRF/HTTPS; all subjects, Year1 KP2027
   and timetable-based RPH Hari Ini. Validate Web/Telegram source parity.
7. Obtain explicit production rollout approval after all tests; merge PR
   and publish in controlled Telegram/Web sequence with rollback available.

## Hard gates

- The draft Google OAuth PR must remain **unmerged** until shared account,
  native document and billing behavior pass E2E; no production config changes.
- Google-only staging session cannot set Telegram's legacy session cookie.
- No real payments are requested on staging.
- SOW/RPT/SK/SP lesson identities stay sourced from approved verified DB,
  not generated or guessed at runtime.
