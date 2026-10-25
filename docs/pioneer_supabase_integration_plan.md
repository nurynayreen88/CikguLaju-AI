# Pioneer persistence integration — Supabase (review before applying)

The live app uses `_sb_request` with Supabase subscriptions and `cikgulaju_users`. Local SQLite payment requests are **not** a safe source of permanent Pioneer status across deployments. The separate `pioneer_entitlements.py` SQLite helper in this PR is a prototype only and must not be wired into production.

## Recommended additive table (not applied)

```sql
create table if not exists public.pioneer_entitlements (
  telegram_user_id bigint primary key,
  payment_reference text not null unique,
  amount_rm numeric(10,2) not null check (amount_rm = 20.00),
  approved_by bigint not null,
  approved_at timestamptz not null default now(),
  status text not null default 'PIONEER_LIFETIME'
    check (status = 'PIONEER_LIFETIME')
);
alter table public.pioneer_entitlements enable row level security;
revoke all on public.pioneer_entitlements from anon, authenticated;
-- Only trusted server-side service-role calls should read or write this table.
```

## Verified code integration points in main app.py

- `DONATION_QR_B64` and `send_donation_qr(cid)`: existing embedded DuitNow QR and Telegram photo upload. Reuse QR bytes/file_id, but Pioneer needs its own caption and callback.
- `_new_payment_request(chat_id, message_id, amount=5.00)`: local payment-request intake. Pending records are reused by chat_id irrespective of amount; fix by adding amount/plan-aware matching before using for RM20.
- `_admin_pending_card` and `admin_approve|<id>`: currently hardcoded RM5 / 30 days. Add distinct Pioneer approval action and validate amount = RM20, pending status, receipt evidence, verified transfer and admin identity.
- `_activate_access`: invokes Supabase `rpc/cikgulaju_activate_subscription` with expiring days; never use this to grant Pioneer.
- `_subscription_row` and `_access_info`: live access checks in Supabase; read Pioneer first and return an active lifetime entitlement without expiry. Keep referral/subscription behavior unchanged.
- `_user_access_text`: display Pioneer lifetime status separately.
- Referral VIP wording should change in user-facing strings only; do not rename legacy database keys, enums or callbacks without a compatibility migration.

## Blocking acceptance tests

Verify Supabase project and schema, snapshot/backup production data, apply migration in controlled environment, check role privileges, verify no access via anon/authenticated keys, confirm payment idempotency, duplicate receipt handling, existing RM5 payment flow, referral expiry, user menu, restart, redeploy, rollback and restoration.

No production database mutation, merge or deploy was performed by this document.
