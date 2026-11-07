# CikguLaju Google Login — zero-new-cost production release gate

Status: REVIEW ONLY. This file and PR #450 do not make the Google login live.

## Confirmed facts (7 Nov 2026)

- Main Supabase project `soxakntcanbycjoygrcx` is on **Free** organization plan.
- Free projects do **not** receive the scheduled daily project backups of Pro/Team/Enterprise.
- Audit before Google schema: 48 existing Telegram users, 8 active lifetime entitlements, 0 invalid trial balances, 1 old orphan subscription; keep the orphan for audit, do not delete.
- GitHub Actions with isolated PostgreSQL 17 passed canonical identity, exactly-once RPH, paid entitlement and legacy preservation rehearsals.
- None of that is a recoverable backup of the real production database.

Authoritative documentation:
https://supabase.com/docs/guides/platform/backups
https://supabase.com/docs/guides/platform/migrating-within-supabase/backup-restore

## Required OFF-SITE export before any production schema change

A local operator with the production database password and **Supabase CLI/Docker**
must obtain the actual database connection string through the Supabase dashboard
Connect panel. Use the Session Pooler string by default where direct IPv6 is
unavailable. Never place the connection string, its password, or the exported
SQL files in GitHub, ChatGPT, Render logs, or public storage.

From a private local backup folder, with the same valid connection string
used in each command (shown here as placeholder only), run:

```sh
supabase db dump --db-url "[PRIVATE_CONNECTION_STRING]" -f roles.sql --role-only
supabase db dump --db-url "[PRIVATE_CONNECTION_STRING]" -f schema.sql
supabase db dump --db-url "[PRIVATE_CONNECTION_STRING]" -f data.sql --use-copy --data-only -x "storage.buckets_vectors" -x "storage.vector_indexes"
```

Confirm all three files exist and are non-empty; validate the SQL logically,
record file hashes and timestamp, and keep an encrypted copy **outside** the
production project and repo. To make the backup truly restorable, test restoring
it to a separate PostgreSQL environment under operator control. Never restore
into the currently live production project as a "test". For Storage objects,
perform an independent object-level export because database dumps cover
Storage metadata, not stored PDFs, DOCX and receipt bytes.

The connected Supabase MCP tool **does not provide a downloadable full
database export or restore verification**, so do not claim the backup is done
until the files and restoration evidence exist.

## Release sequence

1. Obtain and verify encrypted, restorable off-site backup.
2. Record baseline counts/constraints; compare to a read-only SQL preflight.
3. Freeze PR #450 and review its three `DRAFT_ONLY_` SQL files against
   current production schema; apply only additive migrations in the documented
   order, with rollback strategy and no table reset or silent backfill.
4. Verify server-only RLS/grants, canonical Google principal, provider UUID,
   private bucket, native Word/PDF and exactly-once credit ledger.
5. Confirm the Google OAuth provider, callback allowlist and test-user behavior
   in **production Supabase**, not staging.
6. Merge the PR only when approved and CI is green. Production Render
   **auto-deploys on commit**; keep both feature flags OFF.
7. Verify the live Web still supports Telegram sign-in, user profile and
   status, RPH generator and payments. Only then enable the Google feature
   flags in a controlled rollout and perform one real Google E2E session.
8. For linked teacher accounts, verify separately authenticated Google and
   Telegram sessions, explicit balance preview, confirmation, lifetime/paid
   status and trial debit exactly once; no email-only linking.

## Known product scope limit

The native Google-only RPH route currently exposes only verified Year 2–6
English/Moral/PJPK/PSV. Linked Telegram users use the original Telegram-backed
Web features. Do not market the Google-only route as full curriculum parity.
