-- DRAFT ONLY: DO NOT APPLY TO LIVE SUPABASE OR RENDER.
-- New Google-only RPH jobs use the SAME production database as Telegram,
-- the SAME already approved native Word/PDF renderer, and a UUID principal.
-- Linked Telegram users remain on their original lifetime/subscription/trial
-- path. No second trial allotment and no fake numeric Telegram identities.
--
-- Requires: reviewed DRAFT_ONLY_web_canonical_identity_449.sql, private
-- Supabase Storage bucket deployment approval, authenticated server endpoints,
-- and a rollback/reconciliation plan before any production activation.
BEGIN;

INSERT INTO storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
SELECT 'cikgulaju-native-web-rph','cikgulaju-native-web-rph',false,15728640,
 ARRAY['application/pdf',
  'application/vnd.openxmlformats-officedocument.wordprocessingml.document']::text[]
WHERE NOT EXISTS (SELECT 1 FROM storage.buckets WHERE id='cikgulaju-native-web-rph');

DO $verify$
BEGIN
 IF NOT EXISTS (
    SELECT 1 FROM storage.buckets WHERE id='cikgulaju-native-web-rph'
      AND public=false AND file_size_limit BETWEEN 15728640 AND 20000000
 ) THEN RAISE EXCEPTION 'Native Web RPH bucket MUST be private'; END IF;
END;
$verify$;

CREATE TABLE IF NOT EXISTS public.cikgulaju_web_rph_jobs (
 id uuid PRIMARY KEY,
 principal_id uuid NOT NULL REFERENCES public.cikgulaju_web_principals(id)
   ON DELETE RESTRICT,
 selection_sha256 text NOT NULL CHECK(selection_sha256 ~ '^[0-9a-f]{64}$'),
 status text NOT NULL DEFAULT 'prepared'
   CHECK (status IN ('prepared','ready')),
 document_manifest_sha256 text CHECK (
   document_manifest_sha256 IS NULL OR document_manifest_sha256 ~ '^[0-9a-f]{64}$'),
 access_mode text CHECK(access_mode IN ('trial','paid')),
 remaining_after integer CHECK (remaining_after BETWEEN 0 AND 10),
 created_at timestamptz NOT NULL DEFAULT now(),
 ready_at timestamptz,
 CONSTRAINT native_job_ready_requires_verified_bundle CHECK (
   (status='prepared' AND document_manifest_sha256 IS NULL
     AND access_mode IS NULL AND remaining_after IS NULL AND ready_at IS NULL)
   OR (status='ready' AND document_manifest_sha256 IS NOT NULL
     AND access_mode IS NOT NULL AND remaining_after IS NOT NULL AND ready_at IS NOT NULL)
 )
);
CREATE INDEX IF NOT EXISTS cikgulaju_web_rph_jobs_owner
 ON public.cikgulaju_web_rph_jobs(principal_id,created_at DESC);
ALTER TABLE public.cikgulaju_web_rph_jobs ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.cikgulaju_web_rph_jobs FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT,UPDATE ON public.cikgulaju_web_rph_jobs TO service_role;

CREATE TABLE IF NOT EXISTS public.cikgulaju_web_rph_ledger (
 principal_id uuid NOT NULL REFERENCES public.cikgulaju_web_principals(id) ON DELETE RESTRICT,
 job_id uuid NOT NULL REFERENCES public.cikgulaju_web_rph_jobs(id) ON DELETE RESTRICT,
 document_manifest_sha256 text NOT NULL
    CHECK(document_manifest_sha256 ~ '^[0-9a-f]{64}$'),
 access_mode text NOT NULL CHECK(access_mode='trial'),
 remaining_after integer NOT NULL CHECK(remaining_after BETWEEN 0 AND 10),
 charged_at timestamptz NOT NULL DEFAULT now(),
 PRIMARY KEY(principal_id,job_id)
);
ALTER TABLE public.cikgulaju_web_rph_ledger ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.cikgulaju_web_rph_ledger FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON public.cikgulaju_web_rph_ledger TO service_role;

CREATE OR REPLACE FUNCTION public.prepare_native_google_web_rph(
 p_principal_id uuid, p_job_id uuid, p_selection_sha256 text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER
SET search_path=public,pg_temp AS $body$
DECLARE v_job public.cikgulaju_web_rph_jobs%ROWTYPE;
BEGIN
 IF current_user <> 'service_role' THEN
    RAISE EXCEPTION 'Private native Web RPH requires service role';
 END IF;
 IF p_principal_id IS NULL OR p_job_id IS NULL OR
    p_selection_sha256 IS NULL OR
    p_selection_sha256 !~ '^[0-9a-f]{64}$' THEN
    RAISE EXCEPTION 'Invalid native RPH job';
 END IF;
 IF NOT EXISTS (
    SELECT 1 FROM public.cikgulaju_web_principals
    WHERE id=p_principal_id AND legacy_telegram_user_id IS NULL)
 THEN
    RAISE EXCEPTION 'Google-only UUID account required for trial route';
 END IF;
 INSERT INTO public.cikgulaju_web_rph_jobs(id,principal_id,selection_sha256)
 VALUES(p_job_id,p_principal_id,p_selection_sha256)
 ON CONFLICT(id) DO NOTHING;
 SELECT * INTO v_job FROM public.cikgulaju_web_rph_jobs WHERE id=p_job_id;
 IF NOT FOUND OR v_job.principal_id <> p_principal_id
      OR v_job.selection_sha256 <> p_selection_sha256
 THEN RAISE EXCEPTION 'Native RPH job ownership or selection collision'; END IF;
 RETURN jsonb_build_object('job_id',v_job.id,'status',v_job.status);
END;
$body$;

CREATE OR REPLACE FUNCTION public.complete_native_google_web_rph(
 p_principal_id uuid, p_job_id uuid, p_manifest_sha256 text
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER
SET search_path=public,storage,pg_temp AS $body$
DECLARE
 v_job public.cikgulaju_web_rph_jobs%ROWTYPE;
 v_balance integer;
 v_word text;
 v_pdf text;
BEGIN
 IF current_user <> 'service_role' THEN
    RAISE EXCEPTION 'Private native Web RPH requires service role';
 END IF;
 IF p_principal_id IS NULL OR p_job_id IS NULL OR
    p_manifest_sha256 IS NULL OR
    p_manifest_sha256 !~ '^[0-9a-f]{64}$'
 THEN RAISE EXCEPTION 'Invalid native RPH completion'; END IF;

 -- Always lock the authoritative principal BEFORE its job, so separate
 -- generation references cannot race and grant more than ten credits.
 SELECT google_only_trial_remaining INTO v_balance
 FROM public.cikgulaju_web_principals
 WHERE id=p_principal_id AND legacy_telegram_user_id IS NULL FOR UPDATE;
 IF NOT FOUND OR v_balance IS NULL OR v_balance NOT BETWEEN 0 AND 10
 THEN RAISE EXCEPTION 'Google-only authoritative trial not found'; END IF;

 SELECT * INTO v_job FROM public.cikgulaju_web_rph_jobs
 WHERE id=p_job_id AND principal_id=p_principal_id FOR UPDATE;
 IF NOT FOUND THEN RAISE EXCEPTION 'Native job does not belong to principal'; END IF;
 IF v_job.status='ready' THEN
    IF v_job.document_manifest_sha256 <> p_manifest_sha256 THEN
       RAISE EXCEPTION 'Completed RPH manifest collision'; END IF;
    RETURN jsonb_build_object('allowed',true,'replayed',true,
       'access_mode',v_job.access_mode,'remaining',v_job.remaining_after,
       'job_id',v_job.id,'status','ready');
 END IF;
 IF v_job.status<>'prepared' THEN RAISE EXCEPTION 'Unexpected job status'; END IF;
 v_word := p_principal_id::text || '/' || p_job_id::text || '.docx';
 v_pdf := p_principal_id::text || '/' || p_job_id::text || '.pdf';
 IF NOT EXISTS (SELECT 1 FROM storage.objects
      WHERE bucket_id='cikgulaju-native-web-rph' AND name=v_word)
    OR NOT EXISTS (SELECT 1 FROM storage.objects
      WHERE bucket_id='cikgulaju-native-web-rph' AND name=v_pdf)
 THEN RAISE EXCEPTION 'Verified Word and PDF BOTH required before debit'; END IF;

 IF v_balance=0 THEN
    RETURN jsonb_build_object('allowed',false,'replayed',false,
       'access_mode','exhausted','remaining',0,
       'job_id',v_job.id,'status','prepared');
 END IF;

 v_balance := v_balance-1;
 UPDATE public.cikgulaju_web_principals
 SET google_only_trial_remaining=v_balance,updated_at=now()
 WHERE id=p_principal_id;
 INSERT INTO public.cikgulaju_web_rph_ledger(
   principal_id,job_id,document_manifest_sha256,access_mode,remaining_after)
 VALUES(p_principal_id,p_job_id,p_manifest_sha256,'trial',v_balance);
 UPDATE public.cikgulaju_web_rph_jobs
 SET status='ready',document_manifest_sha256=p_manifest_sha256,
     access_mode='trial',remaining_after=v_balance,ready_at=now()
 WHERE id=p_job_id AND principal_id=p_principal_id;
 RETURN jsonb_build_object('allowed',true,'replayed',false,
   'access_mode','trial','remaining',v_balance,'job_id',v_job.id,'status','ready');
END;
$body$;

REVOKE ALL ON FUNCTION public.prepare_native_google_web_rph(uuid,uuid,text)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.prepare_native_google_web_rph(uuid,uuid,text)
  TO service_role;
REVOKE ALL ON FUNCTION public.complete_native_google_web_rph(uuid,uuid,text)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.complete_native_google_web_rph(uuid,uuid,text)
  TO service_role;
COMMIT;
