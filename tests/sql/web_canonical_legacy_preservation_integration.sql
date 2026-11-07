-- DISPOSABLE CI ONLY. Never run against the production or staging database.
-- Fixture records were inserted BEFORE draft canonical migrations. Verify
-- migrations preserve original Telegram balances, paid rights and history.
BEGIN;

DO $before$
DECLARE
  v_count integer;
BEGIN
  IF (SELECT trial_remaining FROM public.cikgulaju_users
      WHERE telegram_user_id=900000001) <> 7
     OR (SELECT credits FROM public.cikgulaju_users
      WHERE telegram_user_id=900000001) <> 41
     OR (SELECT trial_remaining FROM public.cikgulaju_users
      WHERE telegram_user_id=900000002) <> 10
  THEN
    RAISE EXCEPTION 'Additive migration altered existing Telegram balances';
  END IF;

  IF NOT EXISTS (
      SELECT 1 FROM public.pioneer_entitlements
      WHERE telegram_user_id=900000001 AND entitlement='PIONEER_LIFETIME'
        AND revoked_at IS NULL AND payment_reference='ci-lifetime-900000001'
  ) THEN
    RAISE EXCEPTION 'Existing lifetime entitlement lost after migration';
  END IF;
  IF NOT EXISTS (
      SELECT 1 FROM public.subscriptions
      WHERE telegram_user_id=900000002 AND status='active'
        AND plan_code='annual' AND expires_at='2030-01-01'::timestamptz
        AND last_payment_reference='ci-sub-paid'
  ) THEN
    RAISE EXCEPTION 'Existing paid subscription changed after migration';
  END IF;
  IF NOT EXISTS (
      SELECT 1 FROM public.subscriptions
      WHERE telegram_user_id=900000003 AND status='active'
        AND expires_at='2023-02-01'::timestamptz
  ) OR EXISTS (
      SELECT 1 FROM public.cikgulaju_users
      WHERE telegram_user_id=900000003
  ) THEN
    RAISE EXCEPTION 'Historic orphan subscription wrongly deleted or reassigned';
  END IF;
  IF NOT EXISTS (
      SELECT 1 FROM public.trial_ledger WHERE telegram_user_id=900000001
        AND reference_id='ci-old-telegram-job'
        AND amount=-3 AND balance_after=7
  ) THEN
    RAISE EXCEPTION 'Original Telegram trial ledger changed after migration';
  END IF;

  SELECT count(*) INTO v_count FROM public.cikgulaju_web_principals;
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Migration silently created or backfilled % canonical principals',v_count;
  END IF;
  SELECT count(*) INTO v_count FROM public.cikgulaju_web_google_identities;
  IF v_count <> 0 THEN
    RAISE EXCEPTION 'Migration silently assigned Google identities';
  END IF;
  RAISE NOTICE 'PASS: additive schema preserves all seeded legacy and orphan records';
END;
$before$;

-- Only the disposable service role can call link/registration RPCs.
ALTER ROLE service_role BYPASSRLS;
GRANT SELECT,UPDATE ON public.cikgulaju_users TO service_role;
GRANT SELECT,INSERT ON public.trial_ledger TO service_role;
GRANT SELECT ON public.pioneer_entitlements,public.subscriptions TO service_role;
SET LOCAL ROLE service_role;

DO $link$
DECLARE
  v_lifetime uuid;
  v_subscription uuid;
  v_result jsonb;
  v_count integer;
BEGIN
  v_lifetime := public.ensure_native_google_web_principal(
      'e1111111-1111-4111-8111-111111111111','lifetime-test@example.com');
  UPDATE public.cikgulaju_web_principals
     SET google_only_trial_remaining=8 WHERE id=v_lifetime;

  v_result := public.link_native_google_telegram_principal(
      v_lifetime,900000001,true,8,7);
  IF v_result->>'linked' <> 'true'
     OR (v_result->>'telegram_remaining_after')::integer <> 5 THEN
    RAISE EXCEPTION 'Lifetime Telegram user failed cumulative trial accounting: %',v_result;
  END IF;

  IF (SELECT trial_remaining FROM public.cikgulaju_users
      WHERE telegram_user_id=900000001) <> 5
     OR (SELECT credits FROM public.cikgulaju_users
      WHERE telegram_user_id=900000001) <> 41 THEN
    RAISE EXCEPTION 'Identity link altered wrong legacy balance or paid credits';
  END IF;
  IF NOT EXISTS (
      SELECT 1 FROM public.pioneer_entitlements
      WHERE telegram_user_id=900000001 AND entitlement='PIONEER_LIFETIME'
        AND revoked_at IS NULL AND payment_reference='ci-lifetime-900000001'
  ) THEN
    RAISE EXCEPTION 'Lifetime entitlement changed during account linking';
  END IF;
  SELECT count(*) INTO v_count FROM public.trial_ledger
     WHERE telegram_user_id=900000001;
  IF v_count <> 2
     OR NOT EXISTS (
        SELECT 1 FROM public.trial_ledger
        WHERE reference_id='ci-old-telegram-job' AND amount=-3 AND balance_after=7
     )
     OR NOT EXISTS (
        SELECT 1 FROM public.trial_ledger
        WHERE reference_id='native-google-link:'||v_lifetime::text
          AND amount=-2 AND balance_after=5
     ) THEN
    RAISE EXCEPTION 'Link duplicated, removed or omitted Telegram ledger history';
  END IF;

  v_result := public.link_native_google_telegram_principal(
      v_lifetime,900000001,true,8,7);
  IF (v_result->>'replayed')::boolean IS DISTINCT FROM true THEN
    RAISE EXCEPTION 'Re-link was not idempotent';
  END IF;
  IF (SELECT count(*) FROM public.trial_ledger
      WHERE telegram_user_id=900000001) <> 2 THEN
    RAISE EXCEPTION 'Re-link double debited legacy ledger';
  END IF;

  v_subscription := public.ensure_native_google_web_principal(
      'e2222222-2222-4222-8222-222222222222','subscriber-test@example.com');
  v_result := public.link_native_google_telegram_principal(
      v_subscription,900000002,true,10,10);
  IF (v_result->>'telegram_remaining_after')::integer <> 10
     OR NOT EXISTS (
       SELECT 1 FROM public.subscriptions
       WHERE telegram_user_id=900000002 AND status='active'
          AND expires_at='2030-01-01'::timestamptz
          AND last_payment_reference='ci-sub-paid'
     ) THEN
    RAISE EXCEPTION 'Paid subscription or free trial was changed by linking';
  END IF;

  IF NOT EXISTS (
      SELECT 1 FROM public.subscriptions WHERE telegram_user_id=900000003
        AND status='active' AND expires_at='2023-02-01'::timestamptz
  ) OR EXISTS (
      SELECT 1 FROM public.cikgulaju_users WHERE telegram_user_id=900000003
  ) THEN
    RAISE EXCEPTION 'Unrelated orphan subscription modified by identity linking';
  END IF;
  RAISE NOTICE 'PASS: lifetime/subscription/orphan records persist, ledger reconciles once';
END;
$link$;

ROLLBACK;
