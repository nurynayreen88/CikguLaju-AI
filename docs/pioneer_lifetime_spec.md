# CikguLaju Pioneer — Implementation Contract

Status: specification only; payment provider and existing database schema must be audited before implementation. Do not deploy or merge without approval.

## Product
- Pioneer: RM20 one-time payment, lifetime unlimited RPH generation while service operates.
- Do not display quota number; admin controls eligibility and closes enrollment.
- Never activate access from payment redirect alone. Verify provider webhook/signature, amount, currency MYR, unique transaction ID and final paid state. Make processing idempotent.
- Store durable `PIONEER_LIFETIME` entitlement in existing persistent database, with immutable transaction reference and audit trail; no expiration. Do not overwrite on subscription expiry, referral rewards, bot restart, database migration or deployment.
- Preserve existing database; backup before migration; additive schema changes only, with rollback plan and post-deploy reconciliation tests.
- Existing referral: 1 successful referred friend = 3 days of premium access, stackable; remove user-facing word "VIP" while preserving historical data keys as needed for compatibility.
- Access precedence: PIONEER_LIFETIME > time-limited referral/subscription > trial.
- User-facing Pioneer screen: "🏆 Jadi Pioneer — RM20 sekali bayar", "Akses unlimited seumur hidup sepanjang perkhidmatan CikguLaju beroperasi", "Tiada bayaran bulanan atau tahunan".
- Payment failure, pending, refunded, disputed or duplicate event must not accidentally grant or remove access. Revocation/refunds require documented admin process and audit.
- Do not hardcode payment credentials; use environment variables and existing payment infrastructure if any.
- Test: payment success/failure/duplicate, replayed webhook, concurrency, referral expiry, subscription expiry, bot restart, migration, rollback and restored backup.

## Implementation checklist
1. Locate existing Telegram menu/router, payment integration, database and referral logic.
2. Add payment integration if none exists, using verified provider.
3. Implement durable entitlement with precedence and transaction log.
4. Update all user-visible VIP wording (without destructive schema renaming).
5. Add admin enrollment close control and test all flows.
6. Only deploy with explicit approval.
