-- Executed only against ephemeral GitHub Actions PostgreSQL.
-- Raise on any violation. Uses no production data or credentials.
DO $test$
DECLARE
  person uuid;
  again uuid;
  payment uuid;
  second_payment uuid;
  reviewed jsonb;
  result jsonb;
  entitlement_count int;
  trial int;
BEGIN
  person := public.ensure_google_web_account(
    '75a93e53-96da-4a72-90c0-7f88063acacb'::uuid, 'Cikgu A');
  again := public.ensure_google_web_account(
    '75a93e53-96da-4a72-90c0-7f88063acacb'::uuid, 'Cikgu A');
  IF person <> again THEN
    RAISE EXCEPTION 'Google login allocated a second account';
  END IF;
  SELECT google_trial_remaining INTO trial FROM public.web_accounts WHERE id=person;
  IF trial <> 10 THEN
    RAISE EXCEPTION 'Google account lost or duplicated the initial trial quota';
  END IF;

  INSERT INTO storage.objects(bucket_id,name)
  VALUES('web-receipts-staging',person::text||'/aaaabbbb-cccc-4ddd-8eee-ffffffffffff.pdf');

  payment := public.submit_web_payment_request(
    person,'rakan_pembangun',1000,
    person::text||'/aaaabbbb-cccc-4ddd-8eee-ffffffffffff.pdf',
    repeat('a',64));
  IF payment IS NULL THEN
    RAISE EXCEPTION 'Payment request missing';
  END IF;
  BEGIN
    PERFORM public.submit_web_payment_request(
      person,'rakan_pembangun',1000,
      person::text||'/aaaabbbb-cccc-4ddd-8eee-ffffffffffff.pdf',
      repeat('a',64));
    RAISE EXCEPTION 'Duplicate pending request incorrectly accepted';
  EXCEPTION WHEN unique_violation THEN
    NULL; -- expected: cannot create two pending requests
  END;

  BEGIN
    PERFORM public.review_web_payment_request(payment,'approve','invalid',NULL);
    RAISE EXCEPTION 'Non-admin review was accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Invalid payment review' THEN
      RAISE;
    END IF;
  END;

  reviewed := public.review_web_payment_request(payment,'approve','telegram:12345678',NULL);
  IF reviewed->>'status' <> 'approved'
     OR (reviewed->>'already_reviewed')::boolean IS NOT FALSE THEN
    RAISE EXCEPTION 'Approval not confirmed';
  END IF;
  result := public.review_web_payment_request(payment,'approve','telegram:12345678',NULL);
  IF result->>'status' <> 'approved'
     OR (result->>'already_reviewed')::boolean IS NOT TRUE THEN
    RAISE EXCEPTION 'Replay was not idempotent';
  END IF;
  SELECT count(*) INTO entitlement_count
  FROM public.web_entitlements WHERE account_id=person;
  IF entitlement_count <> 1 THEN
    RAISE EXCEPTION 'Duplicate entitlement or missing lifetime entitlement';
  END IF;

  BEGIN
    PERFORM public.submit_web_payment_request(
      person,'rakan_pembangun',1000,
      person::text||'/aaaabbbb-cccc-4ddd-8eee-ffffffffffff.pdf',
      repeat('a',64));
    RAISE EXCEPTION 'Second lifetime payment incorrectly accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Lifetime access already active' THEN
      RAISE;
    END IF;
  END;

  INSERT INTO storage.objects(bucket_id,name)
  VALUES('web-receipts-staging',person::text||'/11112222-3333-4444-8555-666677778888.png');
  second_payment := public.submit_web_payment_request(
    person,'monthly',1000,
    person::text||'/11112222-3333-4444-8555-666677778888.png',
    repeat('b',64));
  BEGIN
    PERFORM public.review_web_payment_request(
      second_payment,'reject','telegram:12345678',NULL);
    RAISE EXCEPTION 'Rejection without reason accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Invalid payment review' THEN
      RAISE;
    END IF;
  END;
  reviewed := public.review_web_payment_request(
    second_payment,'reject','telegram:12345678','Resit tidak jelas');
  IF reviewed->>'status' <> 'rejected' THEN
    RAISE EXCEPTION 'Rejection not persisted';
  END IF;
  SELECT count(*) INTO entitlement_count
  FROM public.web_entitlements WHERE account_id=person;
  IF entitlement_count <> 1 THEN
    RAISE EXCEPTION 'Rejected payment improperly granted access';
  END IF;

  -- A rejected request does not block a different corrected receipt.
  INSERT INTO storage.objects(bucket_id,name)
  VALUES('web-receipts-staging',person::text||'/99992222-3333-4444-8555-666677778888.png');
  second_payment := public.submit_web_payment_request(
    person,'monthly',1000,
    person::text||'/99992222-3333-4444-8555-666677778888.png',
    repeat('c',64));
  reviewed := public.review_web_payment_request(
    second_payment,'approve','telegram:12345678',NULL);
  IF reviewed->>'status' <> 'approved' THEN
    RAISE EXCEPTION 'Corrected receipt cannot be approved';
  END IF;
  SELECT count(*) INTO entitlement_count
  FROM public.web_entitlements
  WHERE account_id=person AND plan_code='monthly'
    AND valid_until>valid_from;
  IF entitlement_count <> 1 THEN
    RAISE EXCEPTION 'Approved monthly subscription missing or invalid';
  END IF;

  -- The user must not be able to create a payment for a receipt that does not exist.
  BEGIN
    PERFORM public.submit_web_payment_request(
      person,'annual',6000,
      person::text||'/eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee.jpg',
      repeat('d',64));
    RAISE EXCEPTION 'Missing private Storage receipt was accepted';
  EXCEPTION WHEN raise_exception THEN
    IF SQLERRM <> 'Private receipt not stored' THEN
      RAISE;
    END IF;
  END;
END
$test$;

-- Privileged service role may use the API, browser roles must not.
DO $rls$
BEGIN
  IF has_table_privilege('anon','public.web_accounts','SELECT')
     OR has_table_privilege('authenticated','public.web_account_identities','SELECT')
     OR has_table_privilege('anon','public.web_payment_requests','SELECT')
     OR has_table_privilege('authenticated','public.web_entitlements','INSERT')
     OR has_function_privilege('anon',
       'public.review_web_payment_request(uuid,text,text,text)','EXECUTE')
     OR has_function_privilege('authenticated',
       'public.submit_web_payment_request(uuid,text,integer,text,text)','EXECUTE')
  THEN
    RAISE EXCEPTION 'Sensitive staging account/payment API improperly exposed';
  END IF;
  IF NOT has_table_privilege('service_role','public.web_payment_requests','SELECT')
     OR NOT has_function_privilege('service_role',
       'public.review_web_payment_request(uuid,text,text,text)','EXECUTE')
  THEN
    RAISE EXCEPTION 'Staging backend payment permissions missing';
  END IF;
END
$rls$;
