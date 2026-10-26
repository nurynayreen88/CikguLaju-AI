-- Non-destructive revocation; retains original approved payment record.
ALTER TABLE public.pioneer_entitlements
  ADD COLUMN IF NOT EXISTS revoked_at timestamptz,
  ADD COLUMN IF NOT EXISTS revoked_by bigint;
CREATE OR REPLACE FUNCTION public.revoke_pioneer_entitlement(
  p_telegram_user_id bigint, p_revoked_by bigint
) RETURNS boolean LANGUAGE plpgsql SECURITY DEFINER SET search_path=public AS $$
BEGIN
  IF p_telegram_user_id <= 0 OR p_revoked_by <= 0 THEN
    RAISE EXCEPTION 'Invalid input';
  END IF;
  UPDATE public.pioneer_entitlements
     SET revoked_at=now(), revoked_by=p_revoked_by
   WHERE telegram_user_id=p_telegram_user_id AND entitlement='PIONEER_LIFETIME'
     AND revoked_at IS NULL;
  RETURN FOUND;
END; $$;
REVOKE ALL ON FUNCTION public.revoke_pioneer_entitlement(bigint,bigint) FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.revoke_pioneer_entitlement(bigint,bigint) TO service_role;
CREATE OR REPLACE FUNCTION public.pioneer_early_bird_count()
RETURNS integer LANGUAGE sql SECURITY DEFINER SET search_path=public AS $$
 SELECT count(*)::integer FROM public.pioneer_entitlements
 WHERE entitlement='PIONEER_LIFETIME' AND revoked_at IS NULL;
$$;
REVOKE ALL ON FUNCTION public.pioneer_early_bird_count() FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.pioneer_early_bird_count() TO service_role;
