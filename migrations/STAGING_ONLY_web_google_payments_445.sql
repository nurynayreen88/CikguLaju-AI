-- STAGING ONLY: Google-first Web manual receipt queue.
-- Apply ONLY to a separate staging Supabase instance after review.
-- Existing Telegram payment tables, receipts and entitlement columns are untouched.
BEGIN;

CREATE TABLE IF NOT EXISTS public.web_payment_requests (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid NOT NULL REFERENCES public.web_accounts(id) ON DELETE RESTRICT,
    plan_code text NOT NULL CHECK (plan_code IN ('rakan_pembangun','monthly','annual')),
    quoted_amount_sen integer NOT NULL CHECK (quoted_amount_sen > 0),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','rejected')),
    receipt_storage_path text NOT NULL UNIQUE CHECK (length(receipt_storage_path) BETWEEN 10 AND 500),
    receipt_sha256 text NOT NULL CHECK (receipt_sha256 ~ '^[a-f0-9]{64}$'),
    submitted_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz,
    reviewed_by text,
    review_note text,
    approved_entitlement_id uuid UNIQUE,
    CHECK (
      (status = 'pending' AND reviewed_at IS NULL AND reviewed_by IS NULL AND approved_entitlement_id IS NULL)
      OR (status = 'rejected' AND reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL AND approved_entitlement_id IS NULL)
      OR (status = 'approved' AND reviewed_at IS NOT NULL AND reviewed_by IS NOT NULL AND approved_entitlement_id IS NOT NULL)
    )
);

-- Exactly one pending request per account. Rejected users can resubmit.
CREATE UNIQUE INDEX IF NOT EXISTS web_payment_one_pending_per_account
ON public.web_payment_requests(account_id) WHERE status = 'pending';

CREATE TABLE IF NOT EXISTS public.web_entitlements (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid NOT NULL REFERENCES public.web_accounts(id) ON DELETE RESTRICT,
    source_payment_id uuid NOT NULL UNIQUE REFERENCES public.web_payment_requests(id) ON DELETE RESTRICT,
    plan_code text NOT NULL CHECK (plan_code IN ('rakan_pembangun','monthly','annual')),
    valid_from timestamptz NOT NULL DEFAULT now(),
    valid_until timestamptz,
    CHECK ((plan_code = 'rakan_pembangun' AND valid_until IS NULL)
       OR (plan_code <> 'rakan_pembangun' AND valid_until > valid_from))
);

CREATE UNIQUE INDEX IF NOT EXISTS web_one_lifetime_entitlement
ON public.web_entitlements(account_id) WHERE plan_code='rakan_pembangun';

ALTER TABLE public.web_payment_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.web_entitlements ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.web_payment_requests, public.web_entitlements FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.web_payment_requests TO service_role;
GRANT SELECT, INSERT ON public.web_entitlements TO service_role;

-- Review must be executed by trusted server code only, after independently
-- verifying that the actor is an authorized CikguLaju admin.
-- Do not infer admin rights from Google email or browser payload.
-- The server must derive the plan amount from a versioned approved catalog,
-- not user input, and verify receipt exists in PRIVATE staging Storage.
-- For an approved request, a single DB transaction must create entitlement
-- and mark payment approved; replays return the same result without granting
-- duplicate access. For rejected requests, store review reason and allow
-- new submission. Send Telegram admin notifications as a separate
-- retryable outbox event AFTER payment request is durably committed.
-- NEVER send receipt to a teacher's Telegram chat or use chat_id as account ID.
COMMIT;
