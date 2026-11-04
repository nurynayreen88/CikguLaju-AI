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
- This is an unmerged draft: production and Supabase schema are untouched.
- Server-side flag `CIKGULAJU_REFERRAL_POINTS_ENABLED` defaults to `0`.
- Migration `migrations/20261104_private_referral_points.sql` is NOT applied.
- The reward percentage is configured as 20.00% but disabled by default; the award RPC returns `reward_disabled` until explicitly enabled.
- Current subscriptions in the DB use `plan_code=30_days`; annual subscriptions require confirmation of the eventual payment plan code.
- Existing Rakan Pembangun approval is not replaced or weakened; after the approval succeeds, the referral wrapper requests an additional verified award. If referral logic fails, payment approval remains effective.

## Required configuration before testing on staging
1. Audit, then apply the additive SQL migration to a staging DB (never overwrite existing users or payment data).
2. Configure a Telegram webhook secret (min. 16 characters) as `CIKGULAJU_TELEGRAM_WEBHOOK_SECRET` in staging AND register the same value with Telegram's `setWebhook(secret_token=...)`. This is mandatory: the module refuses to install when missing and rejects requests with an invalid secret. Existing `/setup-webhook` does NOT set a secret, so do not call it after securing this webhook; update that deployment flow before production.
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
- The Telegram wrapper requires a header secret because the existing webhook does not currently check it. This must be independently configured with Telegram before any live trial.
- The points ledger uses distinct IDs and immutable official payment references; local SQLite request IDs are not the source of truth for award verification.
- The legacy code still exists for backward compatibility while the feature is disabled.
