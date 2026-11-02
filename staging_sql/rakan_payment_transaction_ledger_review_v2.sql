-- STAGING REVIEW ONLY: do not apply to production.
-- Tighten the proposed ledger so a unique transaction can be claimed once.
-- This file is not a migration. Requires review of existing schema and RPC.
CREATE TABLE public.rakan_payment_transaction_ledger (
  id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  provider text NOT NULL CHECK (provider = upper(btrim(provider)) AND length(provider) BETWEEN 2 AND 32),
  merchant_account_key text NOT NULL CHECK (length(btrim(merchant_account_key)) > 0),
  bank_transaction_reference text NOT NULL CHECK (
    bank_transaction_reference = upper(btrim(bank_transaction_reference))
    AND bank_transaction_reference ~ '^[A-Z0-9][A-Z0-9/_-]{5,99}$'
  ),
  payment_request_id bigint NOT NULL CHECK (payment_request_id > 0),
  telegram_user_id bigint NOT NULL CHECK (telegram_user_id > 0),
  amount_rm numeric(10,2) NOT NULL CHECK (amount_rm = 10.00),
  verified_by bigint NOT NULL CHECK (verified_by > 0),
  verified_at timestamptz NOT NULL DEFAULT now(),
  created_at timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT rakan_transaction_once UNIQUE (provider, merchant_account_key, bank_transaction_reference),
  CONSTRAINT rakan_request_once UNIQUE (payment_request_id)
);
ALTER TABLE public.rakan_payment_transaction_ledger ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.rakan_payment_transaction_ledger FROM PUBLIC, anon, authenticated;
-- Never expose a public SECURITY DEFINER RPC that accepts arbitrary admin IDs.
-- The transaction-claim/grant operation must be restricted to a trusted server role.
-- Keep existing pioneer_entitlements constraints intact. No historical backfill
-- is safe until old bank references can be independently matched.
