# Private Referral Points — Draft / Feature OFF by default

## Intent
- A closed, invite-only referral scheme for selected CikguLaju users.
- Referral link: `https://t.me/<bot-username>?start=rp_<opaque-code>`.
- Only users admitted by the admin can view/share their unique code with `/mata`.
- A newly registered user is permanently attributed to the first valid invite code.
- **Registration by itself earns ZERO points.** Points are credited only after an admin-approved payment appears in the existing authoritative Supabase payment/entitlement tables.
- Referral points are **not** RPH trial credits, subscription days, VIP status, cash, or a monetary obligation. No redemption function is enabled.
- Reward is 20% of each verified payment value (RM10 → 2 points; RM8 → 1.6 points; RM50 → 10 points). First confirmed purchase per referred user earns points **once**; recurring payments do not double count in this draft.
- Old `/start ref_<numeric-id>` links stop creating +3 VIP days *only after this replacement feature is enabled*. Historical VIP entitlements are not changed.

## Status
- This is an opt-in implementation. The additive database schema was applied to CikguLaju Supabase on 2026-11-04; referral points remain disabled until rollout.
- Server-side flag `CIKGULAJU_REFERRAL_POINTS_ENABLED` defaults to `0`.
- Migration `migrations/20261104_private_referral_points.sql` was applied to the CikguLaju Supabase project as `private_referral_points_20pct_20261104`.
- The reward percentage is configured as 20.00% but disabled by default; the award RPC returns `reward_disabled` until explicitly enabled.
- Current subscriptions in the DB use `plan_code=30_days`; annual subscriptions require confirmation of the eventual payment plan code.
- Existing Rakan Pembangun approval is not replaced or weakened; after the approval succeeds, the referral wrapper requests an additional verified award. If referral logic fails, payment approval remains effective.

## Required configuration before testing on staging
1. Database schema has been added non-destructively to CikguLaju Supabase. Test only with non-payable fake IDs and dedicated controlled signups; never overwrite existing user or payment data.
2. Configure `CIKGULAJU_TELEGRAM_WEBHOOK_SECRET` (16-256 characters, URL-safe) in the Render service. When the module is enabled it registers Telegram `setWebhook(secret_token=...)` before enabling strict webhook verification. On failure it leaves the referral feature uninstalled. While enabled the obsolete public `/setup-webhook` route is blocked to prevent resetting the secret.
3. Verify the 20.00% setting in `referral_reward_settings`; retain `enabled=false` until all tests pass. Monthly and yearly rewards use the verified payment amount; current Rakan Pembangun amount is RM10.
4. Enable `CIKGULAJU_REFERRAL_POINTS_ENABLED=1` **only in staging**.
5. Admin can privately run `/refadd <TelegramID>` (add/enable member) or `/refdel <TelegramID>` (disable); no public navigation button is added. Whitelisted members view `/mata`.
6. Test first-time registration vs existing account, self-referral, invalid code, duplicate links, paid/unpaid, Rakan Pembangun, monthly, annual, replaying approval, concurrent approval, refunds/revocations, and a deployment restart.
7. Review subscription recording and API exposure under RLS. Confirm a staging webhook calls the opt-in wrapper.
8. After passing tests, plan a separate reviewed production migration and deployment.

## Important limits and next steps
- No historic backfill or automatic expiry/withdrawal of points. Reversals/chargebacks need an audited admin adjustment mechanism before redemptions are introduced.
- Referrer access is manual/whitelisted. No invite is generated for ordinary users.
- The percentage is fixed at 20%. Only future redemption policy needs a separate admin decision.
- Bot-side registration only captures genuinely new accounts created within the last 15 minutes according to the persistent Supabase user table.
- The Telegram wrapper requires and registers a secret header when activated. If registration fails, the feature will refuse to install rather than block normal bot handlers.
- The points ledger uses distinct IDs and immutable official payment references; local SQLite request IDs are not the source of truth for award verification.
- The legacy code still exists for backward compatibility while the feature is disabled.
