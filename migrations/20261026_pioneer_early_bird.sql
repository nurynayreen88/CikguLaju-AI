-- Apply to the existing Supabase database before enabling Early Bird code.
-- Non-destructive: preserves all existing pioneer_entitlements records.
CREATE OR REPLACE FUNCTION public.pioneer_early_bird_count()
RETURNS integer LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
  SELECT count(*)::integer FROM public.pioneer_entitlements
  WHERE entitlement = 'PIONEER_LIFETIME';
$$;

CREATE OR REPLACE FUNCTION public.approve_pioneer_early_bird(
  p_telegram_user_id bigint, p_payment_reference text, p_approved_by bigint
) RETURNS jsonb LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
DECLARE n integer;
BEGIN
  -- Caller must independently authenticate admin and verify payment.
  IF p_telegram_user_id <= 0 OR p_approved_by <= 0 OR nullif(btrim(p_payment_reference),'') IS NULL THEN
    RAISE EXCEPTION 'Invalid pioneer approval input';
  END IF;
  PERFORM pg_advisory_xact_lock(20261026, 500);
  IF EXISTS (SELECT 1 FROM public.pioneer_entitlements WHERE telegram_user_id=p_telegram_user_id) THEN
    RAISE EXCEPTION 'Pioneer entitlement already exists';
  END IF;
  SELECT public.pioneer_early_bird_count() INTO n;
  IF n >= 500 THEN
    RAISE EXCEPTION 'Pioneer Early Bird quota full';
  END IF;
  INSERT INTO public.pioneer_entitlements(telegram_user_id,entitlement,payment_reference,approved_by)
  VALUES(p_telegram_user_id,'PIONEER_LIFETIME',btrim(p_payment_reference),p_approved_by);
  RETURN jsonb_build_object('approved',true,'count',n+1,'remaining',499-n);
END; $$;

-- Restrict direct client execution; service_role is required.
REVOKE ALL ON FUNCTION public.pioneer_early_bird_count() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.approve_pioneer_early_bird(bigint,text,bigint) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.pioneer_early_bird_count() TO service_role;
GRANT EXECUTE ON FUNCTION public.approve_pioneer_early_bird(bigint,text,bigint) TO service_role;
