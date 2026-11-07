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
