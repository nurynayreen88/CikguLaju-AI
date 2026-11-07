-- Disposable PostgreSQL only; never permanently link real staging users from CI.
BEGIN;
DO $test$
DECLARE
  a uuid := gen_random_uuid(); b uuid := gen_random_uuid();
  ga text := gen_random_uuid()::text; gb text := gen_random_uuid()::text;
  res jsonb;
BEGIN
  IF has_function_privilege('anon', 'public.link_verified_telegram_web_account_staging(uuid,bigint)', 'EXECUTE')
     OR has_function_privilege('authenticated', 'public.link_verified_telegram_web_account_staging(uuid,bigint)', 'EXECUTE')
  THEN RAISE EXCEPTION 'Browser may invoke privileged identity link RPC'; END IF;
  INSERT INTO public.web_accounts(id, display_name, google_trial_remaining)
  VALUES (a,'link-test-a',7),(b,'link-test-b',10);
  INSERT INTO public.web_account_identities(provider,subject,account_id)
  VALUES ('google',ga,a),('google',gb,b);
  SELECT public.link_verified_telegram_web_account_staging(a,12345678987654) INTO res;
  IF res->>'linked' <> 'true' THEN RAISE EXCEPTION 'Initial linking failed'; END IF;
  SELECT public.link_verified_telegram_web_account_staging(a,12345678987654) INTO res;
  IF res->>'linked' <> 'true' THEN RAISE EXCEPTION 'Idempotent retry failed'; END IF;
  BEGIN
    PERFORM public.link_verified_telegram_web_account_staging(b,12345678987654);
    RAISE EXCEPTION 'Security failure: duplicate Telegram claim succeeded';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM='Security failure: duplicate Telegram claim succeeded' THEN RAISE; END IF;
  END;
  BEGIN
    PERFORM public.link_verified_telegram_web_account_staging(a,98765432123456);
    RAISE EXCEPTION 'Security failure: reassign Google claim succeeded';
  EXCEPTION WHEN OTHERS THEN
    IF SQLERRM='Security failure: reassign Google claim succeeded' THEN RAISE; END IF;
  END;
  IF (SELECT google_trial_remaining FROM public.web_accounts WHERE id=a)<>7
      OR (SELECT google_trial_remaining FROM public.web_accounts WHERE id=b)<>10
  THEN RAISE EXCEPTION 'Identity link modified existing trial balances'; END IF;
  IF (SELECT COUNT(*) FROM public.web_rph_delivery_ledger WHERE account_id IN (a,b))<>0
  THEN RAISE EXCEPTION 'Identity link wrote to RPH ledger'; END IF;
END;
$test$;
ROLLBACK;
