-- STAGING PROPOSAL ONLY. Do not run against production without a backup and review.
-- Distinguish the immutable bank transaction from a generated entitlement grant ID.
-- This ledger is intentionally separate from existing payment_requests and entitlements.
create table if not exists public.rakan_payment_transaction_ledger (
    id bigint generated always as identity primary key,
    provider text not null,
    merchant_account_key text not null,
    bank_transaction_reference text not null,
    payment_request_id bigint not null,
    telegram_user_id bigint not null,
    amount_rm numeric(10,2) not null check (amount_rm > 0),
    verified_by bigint not null,
    verified_at timestamptz not null default now(),
    created_at timestamptz not null default now(),
    constraint rakan_payment_transaction_unique
      unique (provider, merchant_account_key, bank_transaction_reference),
    constraint rakan_payment_request_unique unique (payment_request_id)
);
-- REQUIRES: transaction reference copied from independently verified TNG Merchant
-- receipt/settlement details, not an arbitrary UUID or Telegram message ID.
-- Transaction reference normalization and transaction-to-grant atomicity must
-- be implemented and tested in the approval RPC before deployment.
-- No permissions granted here: default deny until RPC authorization reviewed.
