# Rakan Pembangun RM10 — staging approval gate

Status: DESIGN ONLY. Do not merge to production.

1. Admin verifies actual TNG Merchant settlement and enters transaction reference and merchant account identity.
2. Normalize reference and validate RM10, payment request ID, Telegram user ID, admin authorization.
3. A single Supabase database transaction must reserve the unique `(provider, merchant_account_key, bank_transaction_reference)` and grant lifetime entitlement for the same user.
4. A duplicate transaction or mismatched request must fail with no entitlement changes.
5. On database failure, keep local request pending and show an actionable error to admin.
6. Mark the local request approved only after the atomic database transaction succeeds.
7. Preserve existing active lifetime entitlements and historical payment references.
8. Test two users presenting the same transaction, two simultaneous approvals, retry after timeout, and rollback after entitlement failure.

Current code does not meet steps 1–4. The UUID fix alone is insufficient. No production migrations or live approval tests have been performed.
