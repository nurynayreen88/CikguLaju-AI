-- Disposable PostgreSQL CI transaction. NO production/staging user debit.
-- Reuse the exact SQL function/migration that will be deployed to staging.
BEGIN;

DO $tests$
DECLARE
    v_trial uuid;
    v_paid uuid;
    v_ref uuid;
    v_reply jsonb;
    v_before integer;
    v_ledger_count integer;
    v_payment uuid;
    v_i integer;
BEGIN
    v_trial := public.ensure_google_web_account(
        '13cefe66-58d1-40b3-8010-ccf20596e456'::uuid, 'CI Trial');
    v_paid := public.ensure_google_web_account(
        '50ca34de-9ae8-49c7-8142-03f3d84ca48c'::uuid, 'CI Paid');

    IF has_function_privilege(
          'anon', 'public.consume_web_rph_bundle_staging(uuid,uuid,text)', 'EXECUTE')
       OR has_function_privilege(
          'authenticated', 'public.consume_web_rph_bundle_staging(uuid,uuid,text)', 'EXECUTE')
       OR has_table_privilege('anon','public.web_rph_delivery_ledger','SELECT')
       OR has_table_privilege('authenticated','public.web_rph_delivery_ledger','INSERT')
    THEN
       RAISE EXCEPTION 'Untrusted browser can access server-only RPH quota';
    END IF;

    SELECT google_trial_remaining INTO v_before
      FROM public.web_accounts WHERE id=v_trial;
    IF v_before <> 10 THEN
        RAISE EXCEPTION 'Trial starting balance not ten';
    END IF;

    -- A full rendered document bundle is one generation regardless of
    -- Word+PDF being downloaded from the same successful generation.
    v_ref := gen_random_uuid();
    v_reply := public.consume_web_rph_bundle_staging(
        v_trial, v_ref, repeat('a',64));
    IF v_reply->>'access_mode' <> 'trial'
       OR (v_reply->>'allowed')::boolean IS DISTINCT FROM TRUE
       OR (v_reply->>'replayed')::boolean IS DISTINCT FROM FALSE
       OR (v_reply->>'remaining')::int <> 9 THEN
        RAISE EXCEPTION 'First successful bundle did not debit precisely once: %', v_reply;
    END IF;

    -- A retry using the SAME server reference has no second charge.
    v_reply := public.consume_web_rph_bundle_staging(
        v_trial, v_ref, repeat('a',64));
    IF (v_reply->>'replayed')::boolean IS DISTINCT FROM TRUE
       OR (v_reply->>'remaining')::int <> 9 THEN
        RAISE EXCEPTION 'Successful generation replay spent credits';
    END IF;
    BEGIN
        PERFORM public.consume_web_rph_bundle_staging(
            v_trial, v_ref, repeat('b',64));
        RAISE EXCEPTION 'Different document under same reference accepted';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'Rendered bundle reference collision' THEN
            RAISE;
        END IF;
    END;
    SELECT count(*) INTO v_ledger_count
      FROM public.web_rph_delivery_ledger WHERE account_id=v_trial;
    IF v_ledger_count <> 1 THEN
        RAISE EXCEPTION 'Replay inserted multiple ledger entries';
    END IF;

    -- Exhaust 10, not 11. Unspent Google staging account is unchanged.
    FOR v_i IN 2..10 LOOP
        v_reply := public.consume_web_rph_bundle_staging(
            v_trial, gen_random_uuid(), repeat('c',64));
        IF (v_reply->>'allowed')::boolean IS DISTINCT FROM TRUE
           OR (v_reply->>'remaining')::int <> 10-v_i THEN
           RAISE EXCEPTION 'Trial remaining miscount at %: %',v_i,v_reply;
        END IF;
    END LOOP;

    v_reply := public.consume_web_rph_bundle_staging(
        v_trial, gen_random_uuid(), repeat('d',64));
    IF (v_reply->>'allowed')::boolean IS DISTINCT FROM FALSE
       OR (v_reply->>'remaining')::int <> 0
       OR v_reply->>'access_mode' <> 'exhausted' THEN
        RAISE EXCEPTION '11th generation not rejected: %', v_reply;
    END IF;
    SELECT count(*) INTO v_ledger_count
      FROM public.web_rph_delivery_ledger WHERE account_id=v_trial;
    IF v_ledger_count <> 10 THEN
        RAISE EXCEPTION 'Exhausted account recorded an 11th generation';
    END IF;
    SELECT google_trial_remaining INTO v_before
      FROM public.web_accounts WHERE id=v_paid;
    IF v_before <> 10 THEN
        RAISE EXCEPTION 'One account debit impacted another account';
    END IF;

    -- Paid privilege MUST originate from a database-reviewed entitlement,
    -- not request JSON, email, Google display label or trial view.
    INSERT INTO storage.objects(bucket_id,name)
       VALUES('web-receipts-staging',
              v_paid::text||'/aaaa1111-bbbb-4ccc-8ddd-999900001111.pdf');
    v_payment := public.submit_web_payment_request(
        v_paid,'rakan_pembangun',1000,
        v_paid::text||'/aaaa1111-bbbb-4ccc-8ddd-999900001111.pdf',
        repeat('e',64));
    PERFORM public.review_web_payment_request(
        v_payment,'approve','telegram:12345678',NULL);
    v_ref := gen_random_uuid();
    v_reply := public.consume_web_rph_bundle_staging(
        v_paid,v_ref,repeat('f',64));
    IF v_reply->>'access_mode' <> 'paid'
       OR (v_reply->>'remaining')::int <> 10
       OR (v_reply->>'allowed')::boolean IS DISTINCT FROM TRUE THEN
        RAISE EXCEPTION 'Confirmed paid entitlement incorrectly debited: %', v_reply;
    END IF;
    v_reply := public.consume_web_rph_bundle_staging(
        v_paid,v_ref,repeat('f',64));
    IF (v_reply->>'replayed')::boolean IS DISTINCT FROM TRUE
       OR (v_reply->>'remaining')::int <> 10 THEN
        RAISE EXCEPTION 'Paid replay not idempotent';
    END IF;

    BEGIN
        PERFORM public.consume_web_rph_bundle_staging(
            gen_random_uuid(), gen_random_uuid(), repeat('a',64));
        RAISE EXCEPTION 'Unknown account accepted';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'Verified Google Web account missing' THEN
            RAISE;
        END IF;
    END;
    BEGIN
        PERFORM public.consume_web_rph_bundle_staging(
            v_trial, gen_random_uuid(), 'not-a-hex-digest');
        RAISE EXCEPTION 'Unverified bundle digest accepted';
    EXCEPTION WHEN raise_exception THEN
        IF SQLERRM <> 'Invalid rendered RPH bundle' THEN
            RAISE;
        END IF;
    END;

    RAISE NOTICE 'PASS: one credit per bundle, replay safety, exhaustion, paid access, isolation, RLS';
END;
$tests$;

-- Preserve all fixture and staging rows, including the real Google test user.
ROLLBACK;
