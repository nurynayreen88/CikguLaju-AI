# RPH trial reservation rollout — staging only

Current production behavior (audited 2026-10-28):
- New users: `cikgulaju_users.trial_remaining` defaults to 5.
- `cikgulaju_use_trial` atomically decrements after a successful delivery.
- The eligibility gate reads balance before generation, so concurrent attempts can both start.
- Failed deliveries must never consume a trial.
- Pioneer and permanent VIP bypass the trial debit.

## Required transactional contract

Implement three server-side RPC operations backed by a durable reservation table:
1. `reserve_rph_trial(user_id, request_id)`: atomically lock the user row and reserve one available slot. Repeating the same request ID returns the existing reservation. Deny when available balance (remaining minus live reservations) is zero. Reject mismatched request/user IDs.
2. `commit_rph_trial(user_id, request_id)`: only after Telegram acknowledges successful RPH delivery, atomically transition reserved to committed, decrement `trial_remaining` exactly once, and write one unique `trial_ledger` debit. Repeating the same request ID must not debit twice.
3. `release_rph_trial(user_id, request_id)`: on generation or delivery failure, atomically release only an uncommitted reservation; never refund a committed debit without a separate audited compensation operation.

Use unique request IDs persisted across retries, not a new UUID for each retry. Expired reservations require a recovery procedure that reconciles delivery outcomes; do not silently expire a reservation after an acknowledged Telegram send.

## Production integration requirements

- Apply reserve before any RPH generation across standard, selected-material, and RPH Hari Ini routes.
- Release in every failure path; commit only on confirmed Telegram delivery.
- Never double debit through nested `send_document` wrappers.
- Preserve legacy balances and `trial_ledger`; no reset, no destructive migration.
- Keep Pioneer/VIP bypass and avoid reserving for non-RPH materials.
- Restrict RPC execution to the server-side service role; do not expose privileged mutation to anonymous callers.

## Mandatory staging checks before merge

- Two concurrent requests with 1 trial: at most one reservation succeeds.
- Retry same request: one reservation and one debit.
- Failed generation and failed Telegram send: no debit and capacity restored.
- Successful send: exactly one debit and one ledger entry.
- User at 0: no RPH generation or delivery.
- Pioneer/VIP: no debit.
- Existing users and historical ledger remain unchanged.
- Simulated worker crash between reserve/send/commit: reconciliation documented and tested.

**Do not merge this staging note as a functional fix.** The reservation RPCs and all call-site integrations still need implementation and integration tests.
