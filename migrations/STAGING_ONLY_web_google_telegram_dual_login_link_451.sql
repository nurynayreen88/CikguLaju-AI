-- Staging only: provider linking is server-authorized after two independently verified sessions.
-- Does NOT query production Telegram users, import paid entitlements or modify trial balances.
-- Never run this migration against the authoritative/production project.
BEGIN;
CREATE OR REPLACE FUNCTION public.link_verified_telegram_web_account_staging(
  p_account_id uuid, p_telegram_user_id bigint
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path=public,pg_temp
AS $fn$
DECLARE
  v_legacy bigint;
  v_linked_account uuid;
BEGIN
  IF p_account_id IS NULL OR p_telegram_user_id IS NULL
     OR p_telegram_user_id <= 0 OR p_telegram_user_id > 9223372036854775807 THEN
    RAISE EXCEPTION 'Invalid verified account identity';
  END IF;
  -- Serializes two different Telegram identities attempting to link the same Google account.
  SELECT legacy_telegram_user_id INTO v_legacy
    FROM public.web_accounts WHERE id=p_account_id FOR UPDATE;
  IF NOT FOUND THEN RAISE EXCEPTION 'Google account missing'; END IF;
  IF NOT EXISTS (SELECT 1 FROM public.web_account_identities
                 WHERE provider='google' AND account_id=p_account_id) THEN
    RAISE EXCEPTION 'Google identity not verified for this account';
  END IF;
  IF v_legacy IS NOT NULL AND v_legacy <> p_telegram_user_id THEN
    RAISE EXCEPTION 'Google account already linked to another Telegram identity';
  END IF;
  -- Telegram provider+subject is unique. Never reassign it across Google accounts.
  INSERT INTO public.web_account_identities(provider,subject,account_id)
    VALUES ('telegram',p_telegram_user_id::text,p_account_id)
    ON CONFLICT(provider,subject) DO NOTHING;
  SELECT account_id INTO v_linked_account
    FROM public.web_account_identities
   WHERE provider='telegram' AND subject=p_telegram_user_id::text;
  IF v_linked_account IS DISTINCT FROM p_account_id THEN
    RAISE EXCEPTION 'Telegram identity belongs to another account';
  END IF;
  IF EXISTS (SELECT 1 FROM public.web_account_identities
             WHERE provider='telegram' AND account_id=p_account_id
               AND subject<>p_telegram_user_id::text) THEN
    RAISE EXCEPTION 'Google account already linked to another Telegram identity';
  END IF;
  UPDATE public.web_accounts
     SET legacy_telegram_user_id=p_telegram_user_id,
         updated_at=now()
   WHERE id=p_account_id;
  RETURN jsonb_build_object('linked',true,'staging_only',true,
                            'telegram_user_id',p_telegram_user_id);
END;
$fn$;
REVOKE ALL ON FUNCTION public.link_verified_telegram_web_account_staging(uuid,bigint)
  FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.link_verified_telegram_web_account_staging(uuid,bigint)
  TO service_role;
COMMIT;
