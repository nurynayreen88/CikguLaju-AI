BEGIN;

-- Read the same ledger for claim validation and for both dashboards.
CREATE FUNCTION public.affiliate_point_summary(p_user bigint)
RETURNS TABLE (earned numeric, reserved numeric, paid numeric, balance numeric, available numeric)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
    WITH credits AS (
        SELECT coalesce(sum(e.points_delta), 0) AS points
        FROM public.referral_point_events e
        WHERE e.referrer_user_id = p_user AND NOT EXISTS (
            SELECT 1 FROM public.affiliate_point_reversals r WHERE r.event_id = e.id
        )
    ), claims AS (
        SELECT coalesce(sum(c.points) FILTER (WHERE c.status IN ('pending','processing')), 0) AS reserved,
               coalesce(sum(c.points) FILTER (WHERE c.status = 'paid'), 0) AS paid
        FROM public.affiliate_claims c
        WHERE c.user_id = p_user AND c.status IN ('pending','processing','paid')
    )
    SELECT credits.points, claims.reserved, claims.paid,
           greatest(credits.points - claims.paid, 0), credits.points - claims.paid - claims.reserved
    FROM credits CROSS JOIN claims;
$$;

CREATE OR REPLACE FUNCTION public.affiliate_balance(p_user bigint)
RETURNS numeric LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
    SELECT s.available FROM public.affiliate_point_summary(p_user) s;
$$;

CREATE OR REPLACE FUNCTION public.affiliate_overview(p_user bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE open_for_claims boolean;
DECLARE rate numeric;
DECLARE summary record;
BEGIN
    SELECT affiliate_claims_enabled, reward_percent INTO open_for_claims, rate
    FROM public.referral_reward_settings WHERE id=1;
    IF open_for_claims IS DISTINCT FROM true OR NOT EXISTS (
        SELECT 1 FROM public.cikgulaju_users WHERE telegram_user_id=p_user
    ) THEN RETURN jsonb_build_object('open',false); END IF;
    SELECT * INTO summary FROM public.affiliate_point_summary(p_user);
    RETURN jsonb_build_object(
        'open',true,'rate',rate,
        'account_number',(SELECT account_number FROM public.affiliate_wallets WHERE user_id=p_user),
        'available',greatest(summary.available,0)::text,
        'balance',summary.balance,'earned',summary.earned,'paid',summary.paid,'reserved',summary.reserved,
        'claims',coalesce((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.requested_at DESC, c.id DESC) FROM (
            SELECT id,points,status,requested_at,paid_at,payment_reference,rejection_reason
            FROM public.affiliate_claims WHERE user_id=p_user ORDER BY requested_at DESC,id DESC LIMIT 50
        ) c),'[]'::jsonb));
END $$;

CREATE FUNCTION public.affiliate_admin_members(p_page integer, p_page_size integer)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
    WITH bounds AS (
        SELECT greatest(p_page, 0)::bigint AS page, least(greatest(p_page_size, 1), 25) AS size
    ), page_members AS MATERIALIZED (
        SELECT m.referrer_user_id, m.enabled, m.created_at
        FROM public.referral_members m
        ORDER BY m.created_at DESC, m.referrer_user_id DESC
        LIMIT (SELECT size + 1 FROM bounds) OFFSET (SELECT page * size FROM bounds)
    ), visible_members AS (
        SELECT * FROM page_members ORDER BY created_at DESC, referrer_user_id DESC
        LIMIT (SELECT size FROM bounds)
    )
    SELECT jsonb_build_object(
        'items', coalesce(jsonb_agg(jsonb_build_object(
            'user_id', m.referrer_user_id::text, 'enabled', m.enabled,
            'first_name', left(u.first_name, 100), 'username', left(u.username, 64),
            'registered_count', (SELECT count(*) FROM public.referral_signups r WHERE r.referrer_user_id = m.referrer_user_id),
            'payment_count', (SELECT count(*) FROM public.referral_point_events e WHERE e.referrer_user_id = m.referrer_user_id),
            'balance', s.balance, 'earned', s.earned, 'paid', s.paid,
            'reserved', s.reserved, 'available', greatest(s.available, 0)
        ) ORDER BY m.created_at DESC, m.referrer_user_id DESC), '[]'::jsonb),
        'more', (SELECT count(*) FROM page_members) > (SELECT size FROM bounds)
    )
    FROM visible_members m
    JOIN public.cikgulaju_users u ON u.telegram_user_id = m.referrer_user_id
    CROSS JOIN LATERAL public.affiliate_point_summary(m.referrer_user_id) s;
$$;

REVOKE ALL ON FUNCTION public.affiliate_point_summary(bigint), public.affiliate_admin_members(integer,integer)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.affiliate_point_summary(bigint), public.affiliate_admin_members(integer,integer)
    TO service_role;
COMMIT;
