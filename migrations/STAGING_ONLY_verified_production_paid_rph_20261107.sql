-- STAGING ONLY: additive lifetime/subscription RPH completion path.
-- NEVER run in production Supabase. Keep existing trial RPC unchanged.
-- Caller is the trusted staging Flask server AFTER a fresh, authenticated
-- private production entitlement lookup for exactly this linked Telegram UID.
-- RPC cannot be used by anon/authenticated/browser. No production writes.
BEGIN;

CREATE OR REPLACE FUNCTION public.complete_web_rph_bundle_prod_paid_staging(
 p_account_id uuid,
 p_job_id uuid,
 p_manifest_sha256 text,
 p_telegram_user_id bigint
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER
SET search_path=public,storage,pg_temp AS $body$
DECLARE
 v_job public.web_rph_bundle_jobs%ROWTYPE;
 v_ledger public.web_rph_delivery_ledger%ROWTYPE;
 v_remaining integer;
 v_word text;
 v_pdf text;
BEGIN
 IF p_account_id IS NULL OR p_job_id IS NULL
    OR p_manifest_sha256 IS NULL
    OR p_manifest_sha256 !~ '^[0-9a-f]{64}$'
    OR p_telegram_user_id IS NULL OR p_telegram_user_id <= 0
 THEN RAISE EXCEPTION 'Invalid production-paid staging RPH request'; END IF;

 -- Access must be via server's secret service role only.
 IF current_user <> 'service_role' THEN
   RAISE EXCEPTION 'Private paid completion requires service role';
 END IF;

 -- Same lock order as the existing complete_web_rph_bundle_staging RPC.
 SELECT * INTO v_job FROM public.web_rph_bundle_jobs
  WHERE id=p_job_id AND account_id=p_account_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Private RPH job not found'; END IF;
 IF v_job.status='ready' THEN
    IF v_job.document_manifest_sha256 <> p_manifest_sha256
    THEN RAISE EXCEPTION 'Previously ready job manifest mismatch'; END IF;
    RETURN jsonb_build_object('allowed',true,'replayed',true,
      'access_mode',v_job.access_mode,'remaining',v_job.remaining_after,
      'job_id',v_job.id,'status','ready');
 END IF;
 IF v_job.status <> 'prepared' THEN
   RAISE EXCEPTION 'Unexpected prepared state';
 END IF;

 SELECT a.google_trial_remaining INTO v_remaining
   FROM public.web_accounts a
   WHERE a.id=p_account_id
     AND a.legacy_telegram_user_id=p_telegram_user_id
   FOR UPDATE;
 IF NOT FOUND OR v_remaining IS NULL OR v_remaining NOT BETWEEN 0 AND 10
 THEN RAISE EXCEPTION 'Linked staging account balance or identity not verified';
 END IF;

 -- No ID from browser: the staging server verified Widget/OAuth and linkage;
 -- the database additionally requires both canonical provider mappings.
 IF NOT EXISTS (
      SELECT 1 FROM public.web_account_identities
      WHERE account_id=p_account_id AND provider='telegram'
        AND subject=p_telegram_user_id::text
    ) OR NOT EXISTS (
      SELECT 1 FROM public.web_account_identities
      WHERE account_id=p_account_id AND provider='google'
    )
 THEN RAISE EXCEPTION 'Exact Google-Telegram identity link required'; END IF;

 -- Word & PDF must already exist in PRIVATE storage, like the trial RPC.
 v_word := p_account_id::text || '/' || p_job_id::text || '.docx';
 v_pdf := p_account_id::text || '/' || p_job_id::text || '.pdf';
 IF NOT EXISTS (
   SELECT 1 FROM storage.objects
   WHERE bucket_id='web-rph-bundles-staging' AND name=v_word
 ) OR NOT EXISTS (
   SELECT 1 FROM storage.objects
   WHERE bucket_id='web-rph-bundles-staging' AND name=v_pdf
 )
 THEN RAISE EXCEPTION 'Both private Word and PDF files are required'; END IF;

 -- Never decrement google_trial_remaining for externally verified paid jobs.
 SELECT * INTO v_ledger FROM public.web_rph_delivery_ledger
  WHERE account_id=p_account_id AND generation_ref=p_job_id;
 IF FOUND THEN
   IF v_ledger.document_manifest_sha256 <> p_manifest_sha256
      OR v_ledger.access_mode <> 'paid'
   THEN RAISE EXCEPTION 'Existing ledger cannot be overwritten'; END IF;
   v_remaining := v_ledger.remaining_after;
 ELSE
   INSERT INTO public.web_rph_delivery_ledger (
     account_id,generation_ref,document_manifest_sha256,
     access_mode,remaining_after
   ) VALUES (
     p_account_id,p_job_id,p_manifest_sha256,'paid',v_remaining
   );
 END IF;

 UPDATE public.web_rph_bundle_jobs
 SET status='ready',document_manifest_sha256=p_manifest_sha256,
     access_mode='paid',remaining_after=v_remaining,ready_at=now()
 WHERE id=p_job_id AND account_id=p_account_id;

 RETURN jsonb_build_object('allowed',true,'replayed',false,
   'access_mode','paid','remaining',v_remaining,
   'job_id',p_job_id,'status','ready');
END;
$body$;

REVOKE ALL ON FUNCTION public.complete_web_rph_bundle_prod_paid_staging(
 uuid,uuid,text,bigint) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.complete_web_rph_bundle_prod_paid_staging(
 uuid,uuid,text,bigint) TO service_role;
COMMIT;
