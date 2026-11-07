-- Disposable CI PostgreSQL. Fake private Storage object metadata ONLY.
-- Does not generate, expose or debit a real user's document.
BEGIN;
DO $test$
DECLARE
 v_account uuid;
 v_other uuid;
 v_job uuid := '97f21ccf-b9b9-48a8-95a9-dae350521a10'::uuid;
 v_job2 uuid := 'cdb182b0-c0ed-40e0-94fa-aed57ce0fdc6'::uuid;
 v_result jsonb;
 v_before integer;
 v_count integer;
BEGIN
  v_account := public.ensure_google_web_account(
     '10300000-2222-4222-8222-222222222222'::uuid, 'Private bundle test');
  v_other := public.ensure_google_web_account(
     '10300000-3333-4333-8333-333333333333'::uuid, 'Other account');

  IF NOT EXISTS (SELECT 1 FROM storage.buckets
       WHERE id='web-rph-bundles-staging' AND public=false) THEN
       RAISE EXCEPTION 'RPH Word/PDF bucket not private';
  END IF;
  IF has_function_privilege('anon','public.complete_web_rph_bundle_staging(uuid,uuid,text)','EXECUTE')
    OR has_function_privilege('authenticated','public.prepare_web_rph_bundle_staging(uuid,uuid,text)','EXECUTE')
    OR has_table_privilege('anon','public.web_rph_bundle_jobs','SELECT')
  THEN RAISE EXCEPTION 'Browser can access privileged file job'; END IF;

  v_result := public.prepare_web_rph_bundle_staging(
      v_account,v_job,repeat('a',64));
  IF v_result->>'status' <> 'prepared' THEN
      RAISE EXCEPTION 'New native bundle not prepared';
  END IF;
  v_result := public.prepare_web_rph_bundle_staging(
      v_account,v_job,repeat('a',64));
  IF v_result->>'status' <> 'prepared' THEN
      RAISE EXCEPTION 'Retry did not preserve job';
  END IF;

  BEGIN
    PERFORM public.prepare_web_rph_bundle_staging(
       v_other,v_job,repeat('a',64));
    RAISE EXCEPTION 'Other account claimed private generation job';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'RPH request identity collision' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.prepare_web_rph_bundle_staging(
       v_account,v_job,repeat('b',64));
    RAISE EXCEPTION 'Same id used for different teaching content';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'RPH request identity collision' THEN RAISE; END IF;
  END;

  BEGIN
    PERFORM public.complete_web_rph_bundle_staging(
       v_account,v_job,repeat('c',64));
    RAISE EXCEPTION 'Bundle charged before verified files exist';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Both private native RPH files must exist' THEN RAISE; END IF;
  END;
  SELECT google_trial_remaining INTO v_before
     FROM public.web_accounts WHERE id=v_account;
  IF v_before <> 10 THEN RAISE EXCEPTION 'Charged without private files'; END IF;

  INSERT INTO storage.objects(bucket_id,name) VALUES
    ('web-rph-bundles-staging',v_account::text||'/'||v_job::text||'.docx');
  BEGIN
    PERFORM public.complete_web_rph_bundle_staging(
       v_account,v_job,repeat('c',64));
    RAISE EXCEPTION 'Bundle charged with missing PDF';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Both private native RPH files must exist' THEN RAISE; END IF;
  END;
  INSERT INTO storage.objects(bucket_id,name) VALUES
    ('web-rph-bundles-staging',v_account::text||'/'||v_job::text||'.pdf');

  v_result := public.complete_web_rph_bundle_staging(
      v_account,v_job,repeat('c',64));
  IF v_result->>'status' <> 'ready'
      OR (v_result->>'allowed')::boolean IS DISTINCT FROM true
      OR (v_result->>'remaining')::int <> 9
      OR (v_result->>'replayed')::boolean IS DISTINCT FROM false
  THEN RAISE EXCEPTION 'Successful bundle must be charged once: %',v_result; END IF;

  v_result := public.complete_web_rph_bundle_staging(
      v_account,v_job,repeat('c',64));
  IF v_result->>'status' <> 'ready'
      OR (v_result->>'remaining')::int <> 9
      OR (v_result->>'replayed')::boolean IS DISTINCT FROM true
  THEN RAISE EXCEPTION 'Safe retry not returning completed files: %',v_result; END IF;
  BEGIN
    PERFORM public.complete_web_rph_bundle_staging(
      v_account,v_job,repeat('d',64));
    RAISE EXCEPTION 'Different Word/PDF manifest reused old job';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'RPH job manifest mismatch' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.complete_web_rph_bundle_staging(
      v_other,v_job,repeat('c',64));
    RAISE EXCEPTION 'Other account finalized private RPH job';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'RPH job not found for verified account' THEN RAISE; END IF;
  END;

  SELECT count(*) INTO v_count
   FROM public.web_rph_delivery_ledger
   WHERE account_id=v_account AND generation_ref=v_job;
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Finalization billed more than one credit';
  END IF;
  SELECT count(*) INTO v_count FROM public.web_rph_bundle_jobs
    WHERE account_id=v_account AND status='ready';
  IF v_count <> 1 THEN
    RAISE EXCEPTION 'Ready private files not durable';
  END IF;

  v_result := public.prepare_web_rph_bundle_staging(
      v_account,v_job2,repeat('e',64));
  IF v_result->>'status' <> 'prepared' THEN
    RAISE EXCEPTION 'Another generation should prepare separately';
  END IF;
  SELECT google_trial_remaining INTO v_before
     FROM public.web_accounts WHERE id=v_account;
  IF v_before <> 9 THEN
    RAISE EXCEPTION 'Preparing a job must not debit';
  END IF;

  RAISE NOTICE 'PASS: private Word/PDF job requires both objects, exactly-once debit, replay and account isolation';
END;
$test$;
ROLLBACK;
