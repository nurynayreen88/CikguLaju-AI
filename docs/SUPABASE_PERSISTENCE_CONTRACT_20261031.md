# CikguLaju AI — Supabase Persistence Contract (2026-10-31)

## Non-destructive rule
Supabase Postgres is the authoritative store for user identity, teacher profiles, entitlements, subscription/payment history, credits, trial consumption, schedules, and generated-RPH history. Application SQLite, local files, process memory, and Render ephemeral disk must not be the only copy of user-owned data. Curriculum SQLite may remain a versioned, read-only content bundle.

## Existing tables (verified 2026-10-31)
- cikgulaju_users (9), teacher_profiles (17), subscriptions (2), subscription_payments (2)
- pioneer_entitlements (2; legacy database label; UI calls this Rakan Pembangun)
- payments (0; credit purchases), pioneer_payment_requests (0)
- trial_ledger (4), credit_ledger (2), rph_generation_history (0), rph_progress (0)

These are table-count observations, not proof of successful application persistence. Do not assume the empty payments table means no subscription payments occurred.

## Implementation checklist (not yet implemented)
1. Trace all writes to bot_users, profile, timetable, holidays, usage, payment, approvals and RPH history. Classify every field by source of truth.
2. Back up existing Supabase tables before schema or data changes; preserve identifiers and transaction references.
3. Add an append-only unified payment event ledger or a read-only UNION view over *verified* payment sources; do not fabricate missing historical receipts. Use idempotent unique provider/reference keys.
4. Record proof references in private storage, not public URLs; restrict access to server-side admin roles.
5. Ensure admin approval and payment-history insertion are atomic, or retryable and idempotent. Never grant access on unverified proof alone.
6. Persist user settings, class lists, timetable and leave confirmations in Supabase before reporting success; reads must survive restart/redeploy.
7. Backfill only after matching existing records by stable Telegram user ID and payment reference. Never reset or truncate.
8. Test payment approval, renewal, trial quota, profile edits and restart persistence on staging before merging to main.
9. Enforce RLS, least privilege and secret-key server-side only. Keep an audit log and tested recovery/backup procedure.

## Deployment gate
No merge to main until existing paid users, subscription rows and all legacy entitlements remain intact; row counts and foreign keys are audited; payment history displays confirmed records; and a restart/redeploy test passes.
