-- DRAFT ONLY. DO NOT APPLY TO ANY SUPABASE PROJECT.
-- Native Google + Telegram dual-login link, both proofs verified by the Web:
-- 1) signed canonical Google UUID session
-- 2) separately verified original Telegram Login Widget session
-- 3) explicit teacher confirmation of trial-balance reconciliation.
-- Accounts are linked by proof, NEVER by matching Google email.
--
-- The original Telegram lifetime/subscriptions are never duplicated, copied,
-- or revoked. One authoritative Telegram trial balance remains after linking.
-- This requires a production snapshot / reviewed rollout before activation.
BEGIN;

CREATE TABLE IF NOT EXISTS public.cikgulaju_web_identity_link_audit (
    principal_id uuid PRIMARY KEY REFERENCES public.cikgulaju_web_principals(id)
      ON DELETE RESTRICT,
    legacy_telegram_user_id bigint NOT NULL UNIQUE
      REFERENCES public.cikgulaju_users(telegram_user_id) ON DELETE RESTRICT,
    google_trial_remaining_before integer NOT NULL
      CHECK(google_trial_remaining_before BETWEEN 0 AND 10),
    telegram_trial_remaining_before integer NOT NULL
      CHECK(telegram_trial_remaining_before BETWEEN 0 AND 10),
    telegram_trial_remaining_after integer NOT NULL
      CHECK(telegram_trial_remaining_after BETWEEN 0 AND 10),
    confirmed_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.cikgulaju_web_identity_link_audit ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.cikgulaju_web_identity_link_audit
  FROM PUBLIC,anon,authenticated;
GRANT SELECT,INSERT ON public.cikgulaju_web_identity_link_audit TO service_role;

CREATE OR REPLACE FUNCTION public.link_native_google_telegram_principal(
    p_principal_id uuid,
    p_telegram_user_id bigint,
    p_merge_confirmed boolean,
    p_expected_google_remaining integer,
    p_expected_telegram_remaining integer
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER
SET search_path=public,pg_temp AS $body$
DECLARE
    v_principal public.cikgulaju_web_principals%ROWTYPE;
    v_original_balance integer;
    v_final_balance integer;
    v_consumed_google integer;
    v_audit public.cikgulaju_web_identity_link_audit%ROWTYPE;
BEGIN
    IF current_user <> 'service_role' THEN
        RAISE EXCEPTION 'Private dual-provider identity link requires service role';
    END IF;
    IF p_principal_id IS NULL OR p_telegram_user_id IS NULL
       OR p_telegram_user_id <= 0 OR p_merge_confirmed IS DISTINCT FROM true
    THEN
        RAISE EXCEPTION 'Both provider proofs and explicit credit consent required';
    END IF;

    -- Same lock order as Google-only RPH completion (principal first).
    SELECT * INTO v_principal FROM public.cikgulaju_web_principals
     WHERE id=p_principal_id FOR UPDATE;
    IF NOT FOUND THEN RAISE EXCEPTION 'Google principal not found'; END IF;

    IF NOT EXISTS (
       SELECT 1 FROM public.cikgulaju_web_google_identities
       WHERE principal_id=p_principal_id)
    THEN RAISE EXCEPTION 'Verified Google subject binding required'; END IF;

    IF v_principal.legacy_telegram_user_id IS NOT NULL THEN
        IF v_principal.legacy_telegram_user_id <> p_telegram_user_id
           OR v_principal.google_only_trial_remaining IS NOT NULL
        THEN RAISE EXCEPTION 'Google principal linked to a different identity'; END IF;
        -- This is a retry. NEVER re-apply credit reconciliation.
        SELECT * INTO v_audit FROM public.cikgulaju_web_identity_link_audit
         WHERE principal_id=p_principal_id
           AND legacy_telegram_user_id=p_telegram_user_id;
        IF NOT FOUND THEN RAISE EXCEPTION 'Existing link requires manual audit'; END IF;
        RETURN jsonb_build_object(
          'linked',true,'replayed',true,
          'telegram_user_id',p_telegram_user_id,
          'telegram_remaining_after',v_audit.telegram_trial_remaining_after,
          'google_remaining_before',v_audit.google_trial_remaining_before);
    END IF;

    -- Do not automatically register Telegram accounts from Google.
    -- Telegram Web widget separately verifies and registers its own users.
    SELECT trial_remaining INTO v_original_balance FROM public.cikgulaju_users
     WHERE telegram_user_id=p_telegram_user_id FOR UPDATE;
    IF NOT FOUND OR v_original_balance NOT BETWEEN 0 AND 10 THEN
        RAISE EXCEPTION 'Verified existing Telegram account required';
    END IF;
    IF v_principal.google_only_trial_remaining IS NULL OR
       v_principal.google_only_trial_remaining NOT BETWEEN 0 AND 10 THEN
        RAISE EXCEPTION 'Google-only trial balance invalid';
    END IF;
    -- The user confirmed a preview of EXACT balances; require those same
    -- balances under row locks to prevent surprise credit changes.
    IF p_expected_google_remaining IS DISTINCT FROM
           v_principal.google_only_trial_remaining
       OR p_expected_telegram_remaining IS DISTINCT FROM v_original_balance
    THEN
        RAISE EXCEPTION 'Link balances changed; preview and consent again';
    END IF;
    IF EXISTS (
       SELECT 1 FROM public.cikgulaju_web_principals
       WHERE legacy_telegram_user_id=p_telegram_user_id
         AND id<>p_principal_id)
    THEN RAISE EXCEPTION 'Telegram identity already belongs to another principal'; END IF;

    -- Used Google trial credits and used Telegram credits are cumulative.
    -- Example: Google used 2, Telegram used 3 -> 10-2-3 = 5 remaining.
    -- No double trial, and NEVER increase the existing Telegram balance.
    v_consumed_google := 10-v_principal.google_only_trial_remaining;
    v_final_balance := GREATEST(0,v_original_balance-v_consumed_google);

    UPDATE public.cikgulaju_users
       SET trial_remaining=v_final_balance,updated_at=now()
     WHERE telegram_user_id=p_telegram_user_id;

    UPDATE public.cikgulaju_web_principals
       SET legacy_telegram_user_id=p_telegram_user_id,
           google_only_trial_remaining=NULL,updated_at=now()
     WHERE id=p_principal_id;

    -- Maintain the ORIGINAL Telegram audit ledger whenever the cumulative
    -- ten-free-generation rule reduces its authoritative trial balance.
    -- In the same database transaction as both account updates. A replay
    -- returns above and cannot insert this record or debit again.
    IF v_final_balance < v_original_balance THEN
        INSERT INTO public.trial_ledger(
            telegram_user_id,amount,reason,reference_id,balance_after)
        VALUES (
            p_telegram_user_id,
            v_final_balance-v_original_balance,
            'Confirmed Google/Telegram trial-credit reconciliation',
            'native-google-link:' || p_principal_id::text,
            v_final_balance);
    END IF;

    INSERT INTO public.cikgulaju_web_identity_link_audit (
       principal_id,legacy_telegram_user_id,
       google_trial_remaining_before,telegram_trial_remaining_before,
       telegram_trial_remaining_after)
    VALUES (p_principal_id,p_telegram_user_id,
       v_principal.google_only_trial_remaining,v_original_balance,v_final_balance);

    RETURN jsonb_build_object(
       'linked',true,'replayed',false,'telegram_user_id',p_telegram_user_id,
       'google_remaining_before',v_principal.google_only_trial_remaining,
       'telegram_remaining_before',v_original_balance,
       'telegram_remaining_after',v_final_balance);
END;
$body$;

REVOKE ALL ON FUNCTION public.link_native_google_telegram_principal(
   uuid,bigint,boolean,integer,integer) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.link_native_google_telegram_principal(
   uuid,bigint,boolean,integer,integer) TO service_role;
COMMIT;
