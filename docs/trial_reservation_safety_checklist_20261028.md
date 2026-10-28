# RPH trial reservation safety acceptance criteria

Do not deploy until all cases pass:

1. Two concurrent requests with one remaining trial: only one reservation succeeds.
2. A retry with the same request ID never creates a second debit.
3. A request ID cannot be reused by another Telegram user.
4. Failed RPH rendering releases the reservation without decrementing balance.
5. Failed Telegram document delivery releases the reservation without decrementing balance.
6. Confirmed Telegram delivery commits exactly once; repeated callbacks are idempotent.
7. VIP and Pioneer access bypasses the free trial debit.
8. Standard, selected and RPH Hari Ini paths use the same reservation lifecycle.
9. A stale reservation is reconciled safely; never release after confirmed delivery without checking delivery evidence.
10. Legacy trial deduction hooks do not double charge.
11. No existing user balance, payment, or curriculum data is reset.
12. Rollback restores prior application behavior without destructive database migration.

Do not claim production readiness from SQL review alone. Run automated tests, verify RPC grants and database integrity, then test on staging before merging.
