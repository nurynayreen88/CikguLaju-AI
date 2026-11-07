-- STAGING ONLY: atomic, replay-safe one-credit debit per fully-rendered RPH bundle.
-- Read-only browser routes NEVER call this. Not a production migration.
-- Apply AFTER staging Google account identity & payment migrations.
-- The signed Google account UUID and server-generated generation ref MUST be
-- validated by the backend; never accept caller-supplied account/ref as authority.
BEGIN;

CREATE TABLE IF NOT EXISTS public.web_rph_delivery_ledger (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    account_id uuid NOT NULL REFERENCES public.web_accounts(id) ON DELETE RESTRICT,
    generation_ref uuid NOT NULL,
    document_manifest_sha256 text NOT NULL
        CHECK (document_manifest_sha256 ~ '^[0-9a-f]{64}$'),
    access_mode text NOT NULL CHECK (access_mode IN ('trial','paid')),
    remaining_after integer NOT NULL CHECK (remaining_after BETWEEN 0 AND 10),
    delivered_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT web_rph_one_charge_per_bundle UNIQUE(account_id, generation_ref)
);
CREATE INDEX IF NOT EXISTS web_rph_ledger_account_history
    ON public.web_rph_delivery_ledger(account_id, delivered_at DESC);

ALTER TABLE public.web_rph_delivery_ledger ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.web_rph_delivery_ledger FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON TABLE public.web_rph_delivery_ledger TO service_role;

-- One generation_ref describes the exact successful bundle (e.g., Word+PDF).
-- An existing ref MUST have identical manifest digest, otherwise error.
-- Lock the authoritative account row BEFORE looking at the ledger: concurrent
-- references serialize, avoiding double-spend or loss of an update.
CREATE OR REPLACE FUNCTION public.consume_web_rph_bundle_staging(
    p_account_id uuid,
    p_generation_ref uuid,
    p_manifest_sha256 text
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = public, pg_temp
AS $body$
DECLARE
    v_remaining integer;
    v_previous public.web_rph_delivery_ledger%ROWTYPE;
    v_paid boolean;
    v_mode text;
BEGIN
    IF p_account_id IS NULL OR p_generation_ref IS NULL
       OR p_manifest_sha256 IS NULL
       OR p_manifest_sha256 !~ '^[0-9a-f]{64}$' THEN
        RAISE EXCEPTION 'Invalid rendered RPH bundle';
    END IF;

    -- All accounts, including paid, must exist. Staging has no production
    -- Telegram IDs or entitlements and MUST NOT invent any.
    SELECT google_trial_remaining INTO v_remaining
      FROM public.web_accounts
     WHERE id = p_account_id FOR UPDATE;
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Verified Google Web account missing';
    END IF;
    IF v_remaining IS NULL OR v_remaining < 0 OR v_remaining > 10 THEN
        RAISE EXCEPTION 'Invalid canonical trial balance';
    END IF;

    SELECT * INTO v_previous
      FROM public.web_rph_delivery_ledger
     WHERE account_id = p_account_id AND generation_ref = p_generation_ref;
    IF FOUND THEN
        IF v_previous.document_manifest_sha256 <> p_manifest_sha256 THEN
            RAISE EXCEPTION 'Rendered bundle reference collision';
        END IF;
        RETURN jsonb_build_object(
            'allowed', true, 'remaining', v_previous.remaining_after,
            'replayed', true, 'access_mode', v_previous.access_mode);
    END IF;

    SELECT EXISTS (
        SELECT 1 FROM public.web_entitlements e
        WHERE e.account_id = p_account_id
          AND e.valid_from <= now()
          AND (
              (e.plan_code = 'rakan_pembangun' AND e.valid_until IS NULL)
              OR (e.plan_code IN ('monthly','annual') AND e.valid_until > now())
          )
    ) INTO v_paid;

    IF NOT v_paid AND v_remaining = 0 THEN
        RETURN jsonb_build_object(
            'allowed', false, 'remaining', 0,
            'replayed', false, 'access_mode', 'exhausted');
    END IF;

    IF v_paid THEN
        v_mode := 'paid';
    ELSE
        v_mode := 'trial';
        v_remaining := v_remaining - 1;
        UPDATE public.web_accounts
           SET google_trial_remaining = v_remaining, updated_at = now()
         WHERE id = p_account_id;
    END IF;

    INSERT INTO public.web_rph_delivery_ledger
        (account_id, generation_ref, document_manifest_sha256,
         access_mode, remaining_after)
    VALUES (p_account_id, p_generation_ref, p_manifest_sha256,
            v_mode, v_remaining);

    RETURN jsonb_build_object(
        'allowed', true, 'remaining', v_remaining,
        'replayed', false, 'access_mode', v_mode);
END;
$body$;

REVOKE ALL ON FUNCTION public.consume_web_rph_bundle_staging(uuid,uuid,text)
  FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.consume_web_rph_bundle_staging(uuid,uuid,text)
  TO service_role;

COMMIT;
