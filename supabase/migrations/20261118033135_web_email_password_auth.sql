-- Shared CikguLaju accounts for Web email/password authentication.
-- Passwords remain in Supabase Auth; this table stores only identity mapping.
CREATE SEQUENCE IF NOT EXISTS public.web_email_account_id_seq
    AS bigint
    START WITH 8000000000000000000
    INCREMENT BY 1
    MINVALUE 8000000000000000000
    MAXVALUE 8999999999999999999
    NO CYCLE;

CREATE TABLE IF NOT EXISTS public.web_email_identities (
    auth_user_id uuid PRIMARY KEY REFERENCES auth.users(id) ON DELETE CASCADE,
    telegram_user_id bigint NOT NULL UNIQUE
        REFERENCES public.cikgulaju_users(telegram_user_id),
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.web_email_identities ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.web_email_identities FROM PUBLIC, anon, authenticated, service_role;
REVOKE ALL ON SEQUENCE public.web_email_account_id_seq FROM PUBLIC, anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.register_web_email_identity(
    p_auth_user_id uuid,
    p_telegram_user_id bigint DEFAULT NULL
)
RETURNS bigint
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = pg_catalog, public
AS $function$
DECLARE
    v_existing_id bigint;
    v_account_id bigint;
BEGIN
    IF p_auth_user_id IS NULL THEN
        RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'INVALID_AUTH_USER';
    END IF;

    PERFORM pg_advisory_xact_lock(hashtextextended(p_auth_user_id::text, 0));

    IF p_telegram_user_id IS NOT NULL THEN
        IF p_telegram_user_id <= 0 OR p_telegram_user_id >= 1000000000000000000 THEN
            RAISE EXCEPTION USING ERRCODE = '22023', MESSAGE = 'INVALID_TELEGRAM_ACCOUNT';
        END IF;
        PERFORM pg_advisory_xact_lock(p_telegram_user_id);
    END IF;

    SELECT telegram_user_id
      INTO v_existing_id
      FROM public.web_email_identities
     WHERE auth_user_id = p_auth_user_id;

    IF FOUND THEN
        IF p_telegram_user_id IS NOT NULL AND v_existing_id <> p_telegram_user_id THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'EMAIL_ACCOUNT_ALREADY_CREATED';
        END IF;
        RETURN v_existing_id;
    END IF;

    IF p_telegram_user_id IS NOT NULL THEN
        IF NOT EXISTS (
            SELECT 1
              FROM public.cikgulaju_users
             WHERE telegram_user_id = p_telegram_user_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'TELEGRAM_ACCOUNT_NOT_FOUND';
        END IF;

        IF EXISTS (
            SELECT 1
              FROM public.web_email_identities
             WHERE telegram_user_id = p_telegram_user_id
        ) THEN
            RAISE EXCEPTION USING ERRCODE = 'P0001', MESSAGE = 'EMAIL_ALREADY_LINKED';
        END IF;

        INSERT INTO public.web_email_identities (auth_user_id, telegram_user_id)
        VALUES (p_auth_user_id, p_telegram_user_id);
        RETURN p_telegram_user_id;
    END IF;

    v_account_id := nextval('public.web_email_account_id_seq'::regclass);
    INSERT INTO public.cikgulaju_users (telegram_user_id)
    VALUES (v_account_id);
    INSERT INTO public.web_email_identities (auth_user_id, telegram_user_id)
    VALUES (p_auth_user_id, v_account_id);

    RETURN v_account_id;
END;
$function$;

REVOKE ALL ON FUNCTION public.register_web_email_identity(uuid, bigint)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.register_web_email_identity(uuid, bigint)
    TO service_role;
