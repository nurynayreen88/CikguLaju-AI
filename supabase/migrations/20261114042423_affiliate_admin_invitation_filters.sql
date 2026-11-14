BEGIN;

CREATE FUNCTION public.affiliate_admin_members(p_page integer, p_page_size integer, p_referral_status text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
    WITH bounds AS (
        SELECT greatest(p_page, 0)::bigint AS page, least(greatest(p_page_size, 1), 25) AS size
    ), referrals AS (
        SELECT s.referrer_user_id, count(*) AS registered_count,
               count(e.id) FILTER (WHERE r.event_id IS NULL) AS payment_count
        FROM public.referral_signups s
        LEFT JOIN public.referral_point_events e
            ON e.referred_user_id = s.referred_user_id AND e.referrer_user_id = s.referrer_user_id
        LEFT JOIN public.affiliate_point_reversals r ON r.event_id = e.id
        GROUP BY s.referrer_user_id
    ), page_members AS MATERIALIZED (
        SELECT m.referrer_user_id, m.enabled, m.created_at,
               coalesce(r.registered_count, 0) AS registered_count,
               coalesce(r.payment_count, 0) AS payment_count
        FROM public.referral_members m
        LEFT JOIN referrals r ON r.referrer_user_id = m.referrer_user_id
        WHERE CASE p_referral_status
            WHEN 'all' THEN true
            WHEN 'registered' THEN r.registered_count > 0
            WHEN 'none' THEN r.registered_count IS NULL
            WHEN 'unpaid' THEN r.registered_count > r.payment_count
            WHEN 'paid' THEN r.payment_count > 0
            ELSE false
        END
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
            'registered_count', m.registered_count, 'payment_count', m.payment_count,
            'balance', s.balance, 'earned', s.earned, 'paid', s.paid,
            'reserved', s.reserved, 'available', greatest(s.available, 0)
        ) ORDER BY m.created_at DESC, m.referrer_user_id DESC), '[]'::jsonb),
        'more', (SELECT count(*) FROM page_members) > (SELECT size FROM bounds)
    )
    FROM visible_members m
    JOIN public.cikgulaju_users u ON u.telegram_user_id = m.referrer_user_id
    CROSS JOIN LATERAL public.affiliate_point_summary(m.referrer_user_id) s;
$$;

REVOKE ALL ON FUNCTION public.affiliate_admin_members(integer,integer,text) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.affiliate_admin_members(integer,integer,text) TO service_role;
COMMIT;
