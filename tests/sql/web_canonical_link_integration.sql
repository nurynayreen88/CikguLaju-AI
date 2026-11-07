-- DISPOSABLE CI ONLY; no mutation of staging or production data.
-- Simulates verified Google + verified Telegram on one production database.
BEGIN;
ALTER ROLE service_role BYPASSRLS;
GRANT SELECT,UPDATE ON public.cikgulaju_users TO service_role;
GRANT SELECT,INSERT ON public.trial_ledger TO service_role;

INSERT INTO public.cikgulaju_users(telegram_user_id,trial_remaining,credits)
VALUES (131321111,7,18),(131322222,10,0);

DO $guard$
BEGIN
 IF has_function_privilege('anon',
   'public.link_native_google_telegram_principal(uuid,bigint,boolean,integer,integer)','EXECUTE')
   OR has_function_privilege('authenticated',
   'public.link_native_google_telegram_principal(uuid,bigint,boolean,integer,integer)','EXECUTE')
 THEN RAISE EXCEPTION 'Public or auth clients can merge identities'; END IF;
 BEGIN
   PERFORM public.link_native_google_telegram_principal(
     '99999999-9999-4999-8999-999999999999',131321111,true,8,7);
   RAISE EXCEPTION 'Non-service role could link accounts';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Private dual-provider identity link requires service role' THEN RAISE; END IF;
 END;
END;
$guard$;

SET LOCAL ROLE service_role;

DO $test$
DECLARE
 v_a uuid;
 v_b uuid;
 v_retry jsonb;
 v_first jsonb;
 v_rem integer;
 v_credit integer;
 v_g_rem integer;
 v_tid bigint;
 v_count integer;
 v_job uuid := '00000000-0000-4000-8000-000000009999';
BEGIN
 v_a := public.ensure_native_google_web_principal(
   'a1e7c000-0000-4000-8000-000000000311','teacher-a@example.com');
 v_b := public.ensure_native_google_web_principal(
   'a1e7c000-0000-4000-8000-000000000322','teacher-b@example.com');
 UPDATE public.cikgulaju_web_principals SET google_only_trial_remaining=8
 WHERE id=v_a; -- Simulates two completed Google-only RPH bundles.
 PERFORM public.prepare_native_google_web_rph(v_a,v_job,repeat('a',64));

 BEGIN
   PERFORM public.link_native_google_telegram_principal(v_a,131321111,false,8,7);
   RAISE EXCEPTION 'No-consent merge unexpectedly permitted';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Both provider proofs and explicit credit consent required'
   THEN RAISE; END IF;
 END;
 BEGIN
   PERFORM public.link_native_google_telegram_principal(v_a,999888777,true,8,7);
   RAISE EXCEPTION 'Unregistered Telegram identity created by Google link';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Verified existing Telegram account required'
   THEN RAISE; END IF;
 END;

 BEGIN
   PERFORM public.link_native_google_telegram_principal(v_a,131321111,true,9,7);
   RAISE EXCEPTION 'Stale credit preview merged accounts';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Link balances changed; preview and consent again'
   THEN RAISE; END IF;
 END;
 SELECT google_only_trial_remaining INTO v_g_rem
   FROM public.cikgulaju_web_principals WHERE id=v_a;
 SELECT trial_remaining INTO v_rem FROM public.cikgulaju_users
   WHERE telegram_user_id=131321111;
 IF v_g_rem <> 8 OR v_rem <> 7 THEN
   RAISE EXCEPTION 'Rejected link changed credit balances';
 END IF;

 v_first:=public.link_native_google_telegram_principal(v_a,131321111,true,8,7);
 IF v_first->>'linked'<>'true'
    OR (v_first->>'replayed')::boolean IS DISTINCT FROM false
    OR (v_first->>'google_remaining_before')::integer<>8
    OR (v_first->>'telegram_remaining_before')::integer<>7
    OR (v_first->>'telegram_remaining_after')::integer<>5
 THEN RAISE EXCEPTION 'Correct one-time cumulative credit merge failed: %',v_first; END IF;

 SELECT legacy_telegram_user_id,google_only_trial_remaining
 INTO v_tid,v_g_rem FROM public.cikgulaju_web_principals WHERE id=v_a;
 SELECT trial_remaining,credits INTO v_rem,v_credit
 FROM public.cikgulaju_users WHERE telegram_user_id=131321111;
 IF v_tid<>131321111 OR v_g_rem IS NOT NULL OR v_rem<>5 OR v_credit<>18
 THEN RAISE EXCEPTION 'Linked primary balance/other credits inconsistent'; END IF;

 -- Two Google trial generations already completed. The original Telegram
 -- ledger must have ONE adjustment (-2), never a duplicate or silent update.
 IF NOT EXISTS (
    SELECT 1 FROM public.trial_ledger
    WHERE telegram_user_id=131321111 AND amount=-2 AND balance_after=5
      AND reference_id='native-google-link:'||v_a::text
 ) THEN RAISE EXCEPTION 'Original Telegram trial reconciliation ledger missing'; END IF;
 v_retry:=public.link_native_google_telegram_principal(v_a,131321111,true,8,7);
 IF (v_retry->>'replayed')::boolean IS DISTINCT FROM true
    OR (v_retry->>'telegram_remaining_after')::integer<>5 THEN
    RAISE EXCEPTION 'Retry of link did not remain idempotent'; END IF;
 SELECT trial_remaining INTO v_rem FROM public.cikgulaju_users
 WHERE telegram_user_id=131321111;
 IF v_rem<>5 THEN RAISE EXCEPTION 'Retry double debited Telegram trial'; END IF;
 SELECT count(*) INTO v_count FROM public.trial_ledger
 WHERE telegram_user_id=131321111 AND reference_id='native-google-link:'||v_a::text;
 IF v_count<>1 THEN RAISE EXCEPTION 'Link replay duplicated trial ledger'; END IF;

 BEGIN
   PERFORM public.link_native_google_telegram_principal(v_a,131322222,true,8,10);
   RAISE EXCEPTION 'Already linked Google identity was reassigned';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Google principal linked to a different identity' THEN RAISE; END IF;
 END;
 BEGIN
   PERFORM public.link_native_google_telegram_principal(v_b,131321111,true,10,5);
   RAISE EXCEPTION 'Telegram user linked to two Google identities';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Telegram identity already belongs to another principal'
   THEN RAISE; END IF;
 END;

 -- Already-prepared Google-only jobs cannot debit after linking. Existing
 -- ready bundles remain stored, for authenticated owner downloads.
 BEGIN
   PERFORM public.complete_native_google_web_rph(v_a,v_job,repeat('b',64));
   RAISE EXCEPTION 'Linked user completed a Google-only trial after merge';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Google-only authoritative trial not found' THEN RAISE; END IF;
 END;

 SELECT count(*) INTO v_count FROM public.cikgulaju_web_identity_link_audit
 WHERE principal_id=v_a AND legacy_telegram_user_id=131321111;
 IF v_count<>1 THEN RAISE EXCEPTION 'Missing unique identity merge audit'; END IF;

 -- Separate fresh Google login can link a different Telegram account safely.
 UPDATE public.cikgulaju_web_principals SET google_only_trial_remaining=10
 WHERE id=v_b;
 v_first:=public.link_native_google_telegram_principal(v_b,131322222,true,10,10);
 IF (v_first->>'telegram_remaining_after')::integer<>10
 THEN RAISE EXCEPTION 'Unused Google trial altered Telegram credits'; END IF;
 SELECT count(*) INTO v_count FROM public.trial_ledger
 WHERE telegram_user_id=131322222;
 IF v_count<>0 THEN RAISE EXCEPTION 'Zero credit adjustment incorrectly recorded as debit'; END IF;

 RAISE NOTICE 'PASS: confirmed dual-proof links, cumulative trial reconciliation, idempotent audit and no fake Telegram user';
END;
$test$;
ROLLBACK;
