-- DISPOSABLE POSTGRES CI ONLY. DO NOT RUN ON PRODUCTION OR STAGING.
-- Test same production-DB Google-only quota with immutable Word+PDF job owner
-- and exactly-once credit consumption. Legacy Telegram quota is not altered.
BEGIN;
ALTER ROLE service_role BYPASSRLS;
GRANT SELECT ON public.cikgulaju_users TO service_role;
GRANT USAGE ON SCHEMA storage TO service_role;
GRANT SELECT,INSERT ON storage.objects TO service_role;
DO $priv$
BEGIN
 IF has_function_privilege('anon',
    'public.complete_native_google_web_rph(uuid,uuid,text)','EXECUTE')
    OR has_function_privilege('authenticated',
    'public.prepare_native_google_web_rph(uuid,uuid,text)','EXECUTE') THEN
      RAISE EXCEPTION 'Native Google RPH RPC exposed to public clients';
 END IF;
 BEGIN
    PERFORM public.prepare_native_google_web_rph(
       '00000000-0000-4000-8000-000000000010'::uuid,
       '00000000-0000-4000-8000-000000000011'::uuid,repeat('a',64));
    RAISE EXCEPTION 'Non-service role prepared RPH';
 EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Private native Web RPH requires service role' THEN
       RAISE;
    END IF;
 END;
END;
$priv$;
-- Legacy Telegram user fixture is populated with a real numeric user ID.
INSERT INTO public.cikgulaju_users(telegram_user_id,trial_remaining)
VALUES (131313131,7);
SET LOCAL ROLE service_role;
DO $verify$
DECLARE
 v_account uuid;
 v_other uuid;
 v_legacy uuid;
 v_job uuid;
 v_result jsonb;
 v_remaining integer;
 v_status text;
 v_count integer;
 i integer;
 v_first_job uuid := '00000000-0000-4000-8000-000000000011';
 v_second_job uuid := '00000000-0000-4000-8000-000000000012';
BEGIN
 v_account := public.ensure_native_google_web_principal(
  '00000000-0000-4000-8000-000000000001','teacher1@example.com');
 v_other := public.ensure_native_google_web_principal(
  '00000000-0000-4000-8000-000000000002','teacher2@example.com');
 INSERT INTO public.cikgulaju_web_principals
     (legacy_telegram_user_id,google_only_trial_remaining)
 VALUES (131313131,NULL) RETURNING id INTO v_legacy;

 BEGIN
   PERFORM public.prepare_native_google_web_rph(
      v_legacy,'00000000-0000-4000-8000-000000000013',repeat('a',64));
   RAISE EXCEPTION 'Linked Telegram account was given second trial channel';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Google-only UUID account required for trial route'
   THEN RAISE; END IF;
 END;
 PERFORM public.prepare_native_google_web_rph(v_account,v_first_job,repeat('a',64));
 PERFORM public.prepare_native_google_web_rph(v_account,v_second_job,repeat('b',64));
 BEGIN
   PERFORM public.prepare_native_google_web_rph(v_other,v_first_job,repeat('a',64));
   RAISE EXCEPTION 'Job ownership collision permitted';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Native RPH job ownership or selection collision' THEN RAISE; END IF;
 END;

 -- Never debit before BOTH private files have been uploaded.
 BEGIN
   PERFORM public.complete_native_google_web_rph(v_account,v_first_job,repeat('c',64));
   RAISE EXCEPTION 'Premature debit before Word+PDF';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Verified Word and PDF BOTH required before debit'
   THEN RAISE; END IF;
 END;
 INSERT INTO storage.objects(bucket_id,name)
 VALUES ('cikgulaju-native-web-rph',v_account::text||'/'||v_first_job::text||'.docx');
 BEGIN
   PERFORM public.complete_native_google_web_rph(v_account,v_first_job,repeat('c',64));
   RAISE EXCEPTION 'Premature debit before PDF';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Verified Word and PDF BOTH required before debit'
   THEN RAISE; END IF;
 END;
 INSERT INTO storage.objects(bucket_id,name)
 VALUES ('cikgulaju-native-web-rph',v_account::text||'/'||v_first_job::text||'.pdf');

 v_result := public.complete_native_google_web_rph(
     v_account,v_first_job,repeat('c',64));
 IF (v_result->>'remaining')::integer <> 9 OR
    (v_result->>'allowed')::boolean IS DISTINCT FROM true OR
    v_result->>'status' <> 'ready'
 THEN RAISE EXCEPTION 'First Google-only bundle not charged once: %',v_result; END IF;
 v_result := public.complete_native_google_web_rph(
     v_account,v_first_job,repeat('c',64));
 IF (v_result->>'remaining')::integer <> 9 OR
    (v_result->>'replayed')::boolean IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'Repeated Google-only bundle charged again: %',v_result; END IF;
 BEGIN
    PERFORM public.complete_native_google_web_rph(v_account,v_first_job,repeat('d',64));
    RAISE EXCEPTION 'Changed ready manifest accepted';
 EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Completed RPH manifest collision' THEN RAISE; END IF;
 END;

 -- Other account must never fetch, finalize or spend the first account job.
 BEGIN
    PERFORM public.complete_native_google_web_rph(v_other,v_first_job,repeat('c',64));
    RAISE EXCEPTION 'Wrong owner finalized protected job';
 EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Native job does not belong to principal' THEN RAISE; END IF;
 END;
 INSERT INTO storage.objects(bucket_id,name) VALUES
   ('cikgulaju-native-web-rph',v_account::text||'/'||v_second_job::text||'.docx'),
   ('cikgulaju-native-web-rph',v_account::text||'/'||v_second_job::text||'.pdf');
 v_result := public.complete_native_google_web_rph(v_account,v_second_job,repeat('e',64));
 IF (v_result->>'remaining')::integer <> 8 THEN
   RAISE EXCEPTION 'Second bundle did not use same trial balance'; END IF;

 FOR i IN 1..8 LOOP
   v_job := ('30000000-0000-4000-8000-'||lpad(i::text,12,'0'))::uuid;
   PERFORM public.prepare_native_google_web_rph(v_account,v_job,repeat('a',64));
   INSERT INTO storage.objects(bucket_id,name) VALUES
     ('cikgulaju-native-web-rph',v_account::text||'/'||v_job::text||'.docx'),
     ('cikgulaju-native-web-rph',v_account::text||'/'||v_job::text||'.pdf');
   v_result := public.complete_native_google_web_rph(v_account,v_job,repeat('c',64));
   IF (v_result->>'allowed')::boolean IS DISTINCT FROM true THEN
     RAISE EXCEPTION 'Trial stopped before tenth completed RPH'; END IF;
 END LOOP;
 SELECT google_only_trial_remaining INTO v_remaining
   FROM public.cikgulaju_web_principals WHERE id=v_account;
 IF v_remaining <> 0 THEN
   RAISE EXCEPTION 'Ten Google-only RPH bundles not exhausted: %',v_remaining;
 END IF;
 v_job := '30000000-0000-4000-8000-000000000099'::uuid;
 PERFORM public.prepare_native_google_web_rph(v_account,v_job,repeat('a',64));
 INSERT INTO storage.objects(bucket_id,name) VALUES
     ('cikgulaju-native-web-rph',v_account::text||'/'||v_job::text||'.docx'),
     ('cikgulaju-native-web-rph',v_account::text||'/'||v_job::text||'.pdf');
 v_result := public.complete_native_google_web_rph(v_account,v_job,repeat('d',64));
 IF (v_result->>'allowed')::boolean IS DISTINCT FROM false OR
    (v_result->>'remaining')::integer <> 0 OR
    v_result->>'status' <> 'prepared' THEN
    RAISE EXCEPTION 'Exhausted user received extra trial: %',v_result;
 END IF;
 SELECT status INTO v_status FROM public.cikgulaju_web_rph_jobs WHERE id=v_job;
 IF v_status <> 'prepared' THEN RAISE EXCEPTION 'Exhausted job became ready'; END IF;
 SELECT count(*) INTO v_count FROM public.cikgulaju_web_rph_ledger WHERE principal_id=v_account;
 IF v_count <> 10 THEN RAISE EXCEPTION 'Not exactly ten credited RPH bundles: %',v_count; END IF;
 SELECT trial_remaining INTO v_remaining FROM public.cikgulaju_users
   WHERE telegram_user_id=131313131;
 IF v_remaining <> 7 THEN
   RAISE EXCEPTION 'Google-only generation debited legacy Telegram user'; END IF;
 RAISE NOTICE 'PASS: ten native Word+PDF bundles, exactly ten credits, no false paid/Telegram access';
END;
$verify$;
ROLLBACK;
