-- CikguLaju private admin user directory.
-- Executable ONLY with server-side service_role; never by browser auth roles.
-- All statuses are derived from active authoritative entitlements; no writes.
CREATE OR REPLACE FUNCTION public.admin_user_directory(
    p_status text DEFAULT 'all',
    p_search text DEFAULT '',
    p_page integer DEFAULT 0
)
RETURNS jsonb
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET search_path = ''
AS $$
DECLARE
    result jsonb;
    query_text text := btrim(coalesce(p_search, ''));
    now_utc timestamptz := now();
BEGIN
    -- Defense in depth beyond the EXECUTE ACL.
    IF current_setting('request.jwt.claim.role', true) IS DISTINCT FROM 'service_role' THEN
        RAISE EXCEPTION 'Admin directory is server only' USING ERRCODE = '42501';
    END IF;
    IF p_status IS NULL OR p_status NOT IN ('all', 'free', 'rakan', 'langganan')
        OR p_page IS NULL OR p_page < 0 OR p_page > 50000
        OR length(query_text) > 100 THEN
        RAISE EXCEPTION 'Invalid directory filter' USING ERRCODE = '22023';
    END IF;

    WITH last_logins AS (
      SELECT e.telegram_user_id, max(e.logged_in_at) AS last_login_at
        FROM public.web_login_events e
       WHERE e.source = 'web'
       GROUP BY e.telegram_user_id
    ), records AS MATERIALIZED (
      SELECT
        u.telegram_user_id,
        CASE WHEN u.telegram_user_id < 1000000000000000000 THEN 'telegram'
             ELSE 'email' END AS account_type,
        CASE WHEN u.telegram_user_id < 1000000000000000000
             THEN u.telegram_user_id::text ELSE NULL END AS telegram_id,
        CASE WHEN a.id IS NOT NULL THEN a.email ELSE NULL END AS email,
        COALESCE(NULLIF(btrim(concat_ws(' ', u.first_name, u.last_name)), ''),
                 NULLIF(u.username, ''),
                 CASE WHEN u.telegram_user_id < 1000000000000000000
                      THEN 'Pengguna Telegram' ELSE 'Pengguna E-mel' END) AS display_name,
        u.created_at AS registered_at,
        l.last_login_at,
        u.trial_remaining,
        CASE WHEN p.telegram_user_id IS NOT NULL
                   AND p.revoked_at IS NULL
                   AND lower(p.entitlement) IN ('lifetime','rakan_pembangun','pioneer_lifetime')
             THEN 'rakan'
             WHEN s.telegram_user_id IS NOT NULL
                  AND s.status = 'active' AND s.expires_at > now_utc
             THEN 'langganan'
             ELSE 'free' END AS access_status,
        CASE WHEN s.status = 'active' AND s.expires_at > now_utc
             THEN s.expires_at ELSE NULL END AS subscription_expires_at
      FROM public.cikgulaju_users u
      LEFT JOIN public.web_email_identities i ON i.telegram_user_id = u.telegram_user_id
      LEFT JOIN auth.users a ON a.id = i.auth_user_id
      LEFT JOIN public.pioneer_entitlements p ON p.telegram_user_id = u.telegram_user_id
      LEFT JOIN public.subscriptions s ON s.telegram_user_id = u.telegram_user_id
      LEFT JOIN last_logins l ON l.telegram_user_id = u.telegram_user_id
    ), filtered AS MATERIALIZED (
      SELECT *
        FROM records r
       WHERE (p_status = 'all' OR r.access_status = p_status)
         AND (query_text = ''
              OR position(lower(query_text) in lower(coalesce(r.email, ''))) > 0
              OR position(lower(query_text) in lower(coalesce(r.telegram_id, ''))) > 0
              OR position(lower(query_text) in lower(r.display_name)) > 0)
    )
    SELECT jsonb_build_object(
       'total', (SELECT count(*) FROM filtered),
       'page', p_page,
       'page_size', 20,
       'items', coalesce(
           (SELECT jsonb_agg(to_jsonb(page_rows) - 'telegram_user_id'
                               ORDER BY page_rows.registered_at DESC,
                                        page_rows.telegram_user_id DESC)
              FROM (
                  SELECT f.account_type, f.telegram_id, f.email, f.display_name,
                         f.registered_at, f.last_login_at, f.trial_remaining,
                         f.access_status, f.subscription_expires_at,
                         f.telegram_user_id
                    FROM filtered f
                   ORDER BY f.registered_at DESC, f.telegram_user_id DESC
                   LIMIT 20 OFFSET (p_page * 20)
              ) AS page_rows),
           '[]'::jsonb)
    ) INTO result;

    RETURN result;
END;
$$;

REVOKE ALL ON FUNCTION public.admin_user_directory(text,text,integer)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.admin_user_directory(text,text,integer)
    TO service_role;
