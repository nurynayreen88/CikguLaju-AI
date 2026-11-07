-- STAGING ONLY, following STAGING_ONLY_web_google_identity_445.sql and
-- STAGING_ONLY_web_google_payments_445.sql. Do not execute in production.
-- Review actions are atomic, idempotent, and accessible to service_role only.

BEGIN;

-- Duplicate receipt content cannot activate more than one payment.
CREATE UNIQUE INDEX IF NOT EXISTS web_payment_unique_receipt_hash
  ON public.web_payment_requests(receipt_sha256);

ALTER TABLE public.web_payment_requests
  ADD CONSTRAINT web_payment_approved_entitlement_fk
  FOREIGN KEY (approved_entitlement_id)
  REFERENCES public.web_entitlements(id) DEFERRABLE INITIALLY DEFERRED;

-- Called by a staging server only after browser authentication and after a
-- private receipt object has been durably uploaded to Supabase Storage.
CREATE OR REPLACE FUNCTION public.submit_web_payment_request(
  p_account_id uuid,
  p_plan_code text,
  p_amount_sen integer,
  p_receipt_path text,
  p_receipt_sha256 text
)
RETURNS uuid LANGUAGE plpgsql SECURITY INVOKER SET search_path = public, storage, pg_temp
AS $body$
DECLARE
  v_id uuid;
BEGIN
  IF p_account_id IS NULL OR p_plan_code NOT IN ('rakan_pembangun','monthly','annual')
     OR p_amount_sen IS NULL OR p_amount_sen < 1 OR p_amount_sen > 10000000
     OR p_receipt_sha256 !~ '^[0-9a-f]{64}$'
     OR p_receipt_path NOT LIKE p_account_id::text || '/%'
     OR length(p_receipt_path) > 500 THEN
    RAISE EXCEPTION 'Invalid verified payment';
  END IF;
  -- No publicly accessible receipt or missing private object accepted.
  IF NOT EXISTS (
    SELECT 1 FROM storage.objects
     WHERE bucket_id='web-receipts-staging' AND name=p_receipt_path
  ) THEN
    RAISE EXCEPTION 'Private receipt not stored';
  END IF;
  IF NOT EXISTS (SELECT 1 FROM public.web_accounts WHERE id=p_account_id) THEN
    RAISE EXCEPTION 'Web account missing';
  END IF;
  IF p_plan_code='rakan_pembangun' AND EXISTS(
    SELECT 1 FROM public.web_entitlements
    WHERE account_id=p_account_id AND plan_code='rakan_pembangun'
  ) THEN
    RAISE EXCEPTION 'Lifetime access already active';
  END IF;
  INSERT INTO public.web_payment_requests
    (account_id,plan_code,quoted_amount_sen,receipt_storage_path,receipt_sha256)
  VALUES (p_account_id,p_plan_code,p_amount_sen,p_receipt_path,p_receipt_sha256)
  RETURNING id INTO v_id;
  RETURN v_id;
END;
$body$;

REVOKE ALL ON FUNCTION public.submit_web_payment_request(uuid,text,integer,text,text)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.submit_web_payment_request(uuid,text,integer,text,text)
  TO service_role;

-- The server MUST first validate that the reviewer is the allowlisted admin
-- authenticated by Telegram widget; no browser-supplied admin IDs.
CREATE OR REPLACE FUNCTION public.review_web_payment_request(
  p_request_id uuid,
  p_action text,
  p_admin_actor text,
  p_note text DEFAULT NULL
)
RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path = public, pg_temp
AS $body$
DECLARE
  v_payment public.web_payment_requests%ROWTYPE;
  v_entitlement uuid;
  v_valid_from timestamptz;
  v_valid_until timestamptz;
  v_duration interval;
BEGIN
  IF p_request_id IS NULL OR p_action NOT IN ('approve','reject')
      OR p_admin_actor !~ '^telegram:[0-9]{4,20}$'
      OR length(coalesce(p_note,'')) > 500
      OR (p_action='reject' AND nullif(btrim(p_note), '') IS NULL) THEN
    RAISE EXCEPTION 'Invalid payment review';
  END IF;

  SELECT * INTO v_payment FROM public.web_payment_requests
   WHERE id=p_request_id FOR UPDATE;
  IF NOT FOUND THEN
    RAISE EXCEPTION 'Payment request missing';
  END IF;
  IF v_payment.status <> 'pending' THEN
    -- Replays never create another entitlement or rewrite an earlier decision.
    RETURN jsonb_build_object('id',v_payment.id,'status',v_payment.status,
                              'already_reviewed',true);
  END IF;

  IF p_action='reject' THEN
    UPDATE public.web_payment_requests
       SET status='rejected', reviewed_at=now(),
           reviewed_by=p_admin_actor,review_note=p_note
     WHERE id=p_request_id;
    RETURN jsonb_build_object('id',p_request_id,'status','rejected',
                              'already_reviewed',false);
  END IF;

  IF v_payment.plan_code='rakan_pembangun' AND EXISTS(
    SELECT 1 FROM public.web_entitlements
     WHERE account_id=v_payment.account_id AND plan_code='rakan_pembangun'
  ) THEN
    RAISE EXCEPTION 'Existing lifetime entitlement requires manual review';
  END IF;
  v_valid_from := now();
  IF v_payment.plan_code='monthly' THEN
    v_duration := interval '1 month';
  ELSIF v_payment.plan_code='annual' THEN
    v_duration := interval '1 year';
  ELSE
    v_duration := NULL;
  END IF;

  IF v_duration IS NOT NULL THEN
    SELECT greatest(v_valid_from,coalesce(max(valid_until),v_valid_from))
      INTO v_valid_from FROM public.web_entitlements
      WHERE account_id=v_payment.account_id AND valid_until IS NOT NULL
            AND valid_until > now();
    v_valid_until := v_valid_from + v_duration;
  ELSE
    v_valid_until := NULL;
  END IF;
  INSERT INTO public.web_entitlements(
    account_id, source_payment_id, plan_code, valid_from, valid_until)
  VALUES (v_payment.account_id,p_request_id,v_payment.plan_code,
          v_valid_from,v_valid_until) RETURNING id INTO v_entitlement;

  UPDATE public.web_payment_requests
     SET status='approved', reviewed_at=now(), reviewed_by=p_admin_actor,
         review_note=p_note, approved_entitlement_id=v_entitlement
   WHERE id=p_request_id;

  RETURN jsonb_build_object('id',p_request_id,'status','approved',
                            'already_reviewed',false);
END;
$body$;

REVOKE ALL ON FUNCTION public.review_web_payment_request(uuid,text,text,text)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.review_web_payment_request(uuid,text,text,text)
  TO service_role;

COMMIT;
