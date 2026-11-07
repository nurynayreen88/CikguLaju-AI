-- Disposable CI only. Does not touch Supabase production or staging.
BEGIN;
DO $test$
DECLARE
  v_google uuid;
  v_legacy uuid;
  v_balance integer;
BEGIN
  INSERT INTO public.cikgulaju_users(telegram_user_id,trial_remaining)
    VALUES (121212121,3);
  INSERT INTO public.cikgulaju_web_principals(legacy_telegram_user_id,google_only_trial_remaining)
    VALUES (121212121,NULL)
    RETURNING id INTO v_legacy;
  INSERT INTO public.cikgulaju_web_principals DEFAULT VALUES
    RETURNING id INTO v_google;

  INSERT INTO public.cikgulaju_web_google_identities(auth_subject,principal_id)
    VALUES('6d6cba47-d17c-4d86-a9da-2c29b2651193',v_google);

  SELECT trial_remaining INTO v_balance
    FROM public.cikgulaju_users WHERE telegram_user_id=121212121;
  IF v_balance <> 3 THEN
    RAISE EXCEPTION 'Legacy Telegram free trial overwritten by UUID migration';
  END IF;
  SELECT google_only_trial_remaining INTO v_balance
    FROM public.cikgulaju_web_principals WHERE id=v_legacy;
  IF v_balance IS NOT NULL THEN
    RAISE EXCEPTION 'Linked legacy ID got a second ten-credit allocation';
  END IF;
  SELECT google_only_trial_remaining INTO v_balance
    FROM public.cikgulaju_web_principals WHERE id=v_google;
  IF v_balance <> 10 THEN
    RAISE EXCEPTION 'Google-only new identity missing separate trial';
  END IF;

  BEGIN
    INSERT INTO public.cikgulaju_web_principals(legacy_telegram_user_id)
      VALUES(121212121);
    RAISE EXCEPTION 'Legacy account duplicated';
  EXCEPTION WHEN check_violation THEN NULL;
  END;
  BEGIN
    INSERT INTO public.cikgulaju_web_principals(legacy_telegram_user_id,google_only_trial_remaining)
      VALUES(121212121,NULL);
    RAISE EXCEPTION 'Second legacy principal inserted';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
  BEGIN
    INSERT INTO public.cikgulaju_web_google_identities(auth_subject,principal_id)
      VALUES('6d6cba47-d17c-4d86-a9da-2c29b2651193',v_legacy);
    RAISE EXCEPTION 'Verified Google identity assigned to two accounts';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;
  BEGIN
    INSERT INTO public.cikgulaju_web_google_identities(auth_subject,principal_id)
      VALUES('3b63463b-72d9-41b7-8e1c-454af691e584',v_google);
    RAISE EXCEPTION 'Second Google subject claimed same principal';
  EXCEPTION WHEN unique_violation THEN NULL;
  END;

  IF has_table_privilege('anon','public.cikgulaju_web_principals','SELECT')
   OR has_table_privilege('authenticated','public.cikgulaju_web_google_identities','INSERT')
   OR NOT has_table_privilege('service_role','public.cikgulaju_web_principals','SELECT') THEN
      RAISE EXCEPTION 'Canonical account privileges fail closed incorrectly';
  END IF;
  IF NOT EXISTS (
     SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid=c.relnamespace
     WHERE n.nspname='public' AND c.relname='cikgulaju_web_principals'
       AND c.relrowsecurity
  ) THEN
      RAISE EXCEPTION 'Canonical principal table RLS missing';
  END IF;

  RAISE NOTICE 'PASS: no duplicate legacy credit, no implicit merging, UUID uniqueness, private RLS';
END;
$test$;
ROLLBACK;

-- A second transaction proves Google-only account signup uses a UUID and
-- exactly one initial trial allocation, with no invented Telegram account.
BEGIN;
-- Disposable CI service_role must behave like Supabase's private bypass role.
ALTER ROLE service_role BYPASSRLS;
-- Only this disposable test fixture needs explicit legacy table grant.
GRANT SELECT ON public.cikgulaju_users TO service_role;
DO $deny$
BEGIN
 IF has_function_privilege('anon',
       'public.ensure_native_google_web_principal(uuid,text)','EXECUTE')
 OR has_function_privilege('authenticated',
       'public.ensure_native_google_web_principal(uuid,text)','EXECUTE')
 OR NOT has_function_privilege('service_role',
       'public.ensure_native_google_web_principal(uuid,text)','EXECUTE') THEN
    RAISE EXCEPTION 'Google canonical signup function privileges are unsafe';
 END IF;
 BEGIN
    PERFORM public.ensure_native_google_web_principal(
       '11111111-1111-4111-8111-111111111111','teacher1@example.com');
    RAISE EXCEPTION 'Non-service role created Google principal';
 EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Private canonical signup requires service role' THEN RAISE; END IF;
 END;
END;
$deny$;
SET LOCAL ROLE service_role;
DO $verify$
DECLARE
 v_first uuid;
 v_repeat uuid;
 v_second uuid;
 v_remaining integer;
 v_tg bigint;
 v_email text;
 v_count integer;
BEGIN
 v_first := public.ensure_native_google_web_principal(
      '11111111-1111-4111-8111-111111111111', 'teacher1@example.com');
 v_repeat := public.ensure_native_google_web_principal(
      '11111111-1111-4111-8111-111111111111', 'teacher1@example.com');
 IF v_first IS NULL OR v_first <> v_repeat THEN
    RAISE EXCEPTION 'Same OAuth identity created multiple accounts';
 END IF;
 SELECT legacy_telegram_user_id, google_only_trial_remaining, google_login_email
 INTO v_tg,v_remaining,v_email FROM public.cikgulaju_web_principals WHERE id=v_first;
 IF v_tg IS NOT NULL OR v_remaining <> 10 OR v_email <> 'teacher1@example.com' THEN
    RAISE EXCEPTION 'Google-only signup produced incorrect account/quota/ID';
 END IF;

 BEGIN
    PERFORM public.ensure_native_google_web_principal(
       '22222222-2222-4222-8222-222222222222', 'teacher1@example.com');
    RAISE EXCEPTION 'Different Google subject seized existing email';
 EXCEPTION WHEN unique_violation THEN NULL;
 END;
 BEGIN
    PERFORM public.ensure_native_google_web_principal(
       '22222222-2222-4222-8222-222222222222', 'TEACHER@EXAMPLE.COM');
    RAISE EXCEPTION 'Unnormalized email accepted';
 EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Invalid verified Google identity' THEN RAISE; END IF;
 END;
 v_second := public.ensure_native_google_web_principal(
      '22222222-2222-4222-8222-222222222222', 'teacher2@example.com');
 IF v_second = v_first THEN RAISE EXCEPTION 'Distinct Google OAuth merged accounts'; END IF;
 v_repeat := public.ensure_native_google_web_principal(
      '11111111-1111-4111-8111-111111111111', 'teacher3@example.com');
 IF v_repeat <> v_first THEN RAISE EXCEPTION 'Verified email change lost account UUID'; END IF;
 SELECT count(*) INTO v_count FROM public.cikgulaju_web_principals
 WHERE google_login_email IS NOT NULL;
 IF v_count <> 2 THEN RAISE EXCEPTION 'Unexpected canonical principals: %',v_count; END IF;
 SELECT count(*) INTO v_count FROM public.cikgulaju_users
 WHERE telegram_user_id IN (11111111,22222222);
 IF v_count <> 0 THEN RAISE EXCEPTION 'Google signup fabricated Telegram account'; END IF;
 RAISE NOTICE 'PASS: Google-only account UUID, one trial, safe verified email change and collision protection';
END;
$verify$;
ROLLBACK;
