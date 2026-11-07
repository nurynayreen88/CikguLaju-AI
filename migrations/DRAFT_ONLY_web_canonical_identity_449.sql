-- DESIGN PROPOSAL ONLY: DO NOT APPLY TO STAGING OR PRODUCTION.
-- New canonical Google-first + existing Telegram account identity scaffold.
-- Verified against READ-ONLY 2026-11-07 metadata of production public.cikgulaju_users:
-- telegram_user_id bigint PRIMARY KEY, trial_remaining integer NOT NULL.
-- No BACKFILL, legacy ALTER, quota copy, entitlement overwrite or default signup.
-- Requires reviewed snapshot, identity link RPC, native generator, RLS/rollback plan.
BEGIN;

CREATE TABLE IF NOT EXISTS public.cikgulaju_web_principals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    -- Verified by the server against the Google OAuth provider identity.
    -- Login label only; do not authorize legacy Telegram access by email.
    google_login_email text UNIQUE,
    legacy_telegram_user_id bigint UNIQUE
        REFERENCES public.cikgulaju_users(telegram_user_id) ON DELETE RESTRICT,
    -- ONLY for Google-only principals. Linked legacy users use the original
    -- cikgulaju_users.trial_remaining instead, so a second ten credits cannot
    -- appear when a Google identity is explicitly linked to Telegram.
    google_only_trial_remaining integer DEFAULT 10,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT verified_login_email_format CHECK (
        google_login_email IS NULL OR
        (google_login_email = lower(google_login_email)
         AND length(google_login_email) BETWEEN 3 AND 254
         AND google_login_email ~ '^[a-z0-9.!#$%&''*+/=?^_`{|}~-]+@[a-z0-9-]+([.][a-z0-9-]+)+
        (legacy_telegram_user_id IS NULL
         AND google_only_trial_remaining BETWEEN 0 AND 10)
        OR (legacy_telegram_user_id IS NOT NULL
            AND google_only_trial_remaining IS NULL)
    )
);

-- Google subject UUID must be independently verified against the *production*
-- Supabase Auth user and provider = google, never browser-provided email/name.
-- Staging project Auth UUIDs are not automatically portable across projects.
CREATE TABLE IF NOT EXISTS public.cikgulaju_web_google_identities (
    auth_subject uuid PRIMARY KEY,
    principal_id uuid NOT NULL UNIQUE
       REFERENCES public.cikgulaju_web_principals(id) ON DELETE RESTRICT,
    verified_at timestamptz NOT NULL DEFAULT now()
);

-- Draft only. The same verified Google provider subject is the stable key;
-- email is a teacher-facing login identifier, not an account merge token.
-- Server MUST verify the Google ID, provider and confirmed email via the
-- Supabase /auth/v1/user endpoint before invoking this private RPC.
CREATE OR REPLACE FUNCTION public.ensure_native_google_web_principal(
    p_auth_subject uuid, p_verified_email text
) RETURNS uuid
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = public, pg_temp AS $body$
DECLARE
    v_principal uuid;
BEGIN
    IF current_user <> 'service_role' THEN
        RAISE EXCEPTION 'Private canonical signup requires service role';
    END IF;
    IF p_auth_subject IS NULL OR p_verified_email IS NULL OR
       length(p_verified_email) NOT BETWEEN 3 AND 254 OR
       p_verified_email <> lower(p_verified_email) OR
       p_verified_email !~ '^[a-z0-9.!#$%&''*+/=?^_`{|}~-]+@[a-z0-9-]+([.][a-z0-9-]+)+
ALTER TABLE public.cikgulaju_web_google_identities ENABLE ROW LEVEL SECURITY;

-- Backend-only. Browser session proves identity to server; the backend maps
-- to UUID and chooses the true credit source (Google-only vs legacy Telegram).
REVOKE ALL ON public.cikgulaju_web_principals,
    public.cikgulaju_web_google_identities FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_principals
    TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_google_identities
    TO service_role;

COMMENT ON TABLE public.cikgulaju_web_principals IS
    'DRAFT: canonical Web principal. Telegram legacy trial, subscription, and lifetime records are authoritative for linked users. No automatic email matching.';
COMMENT ON TABLE public.cikgulaju_web_google_identities IS
    'DRAFT: verified Google provider subject -> one UUID principal. Dual verified sessions and a review-gated link function are required before reassigning an identity.';
COMMIT;
)
    ),
    CONSTRAINT no_duplicate_legacy_trial_allowance CHECK (
        (legacy_telegram_user_id IS NULL
         AND google_only_trial_remaining BETWEEN 0 AND 10)
        OR (legacy_telegram_user_id IS NOT NULL
            AND google_only_trial_remaining IS NULL)
    )
);

-- Google subject UUID must be independently verified against the *production*
-- Supabase Auth user and provider = google, never browser-provided email/name.
-- Staging project Auth UUIDs are not automatically portable across projects.
CREATE TABLE IF NOT EXISTS public.cikgulaju_web_google_identities (
    auth_subject uuid PRIMARY KEY,
    principal_id uuid NOT NULL UNIQUE
       REFERENCES public.cikgulaju_web_principals(id) ON DELETE RESTRICT,
    verified_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.cikgulaju_web_principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cikgulaju_web_google_identities ENABLE ROW LEVEL SECURITY;

-- Backend-only. Browser session proves identity to server; the backend maps
-- to UUID and chooses the true credit source (Google-only vs legacy Telegram).
REVOKE ALL ON public.cikgulaju_web_principals,
    public.cikgulaju_web_google_identities FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_principals
    TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_google_identities
    TO service_role;

COMMENT ON TABLE public.cikgulaju_web_principals IS
    'DRAFT: canonical Web principal. Telegram legacy trial, subscription, and lifetime records are authoritative for linked users. No automatic email matching.';
COMMENT ON TABLE public.cikgulaju_web_google_identities IS
    'DRAFT: verified Google provider subject -> one UUID principal. Dual verified sessions and a review-gated link function are required before reassigning an identity.';
COMMIT;

    THEN
        RAISE EXCEPTION 'Invalid verified Google identity';
    END IF;
    -- Serialize concurrent OAuth callbacks for this exact Google subject.
    PERFORM pg_advisory_xact_lock(hashtextextended(p_auth_subject::text, 94123));
    SELECT principal_id INTO v_principal
      FROM public.cikgulaju_web_google_identities
     WHERE auth_subject = p_auth_subject;
    IF v_principal IS NOT NULL THEN
       -- The same OAuth subject may have its provider-confirmed email updated,
       -- but it cannot claim an email already held by another principal.
       UPDATE public.cikgulaju_web_principals
          SET google_login_email=p_verified_email,updated_at=now()
        WHERE id=v_principal;
       IF NOT FOUND THEN RAISE EXCEPTION 'Orphan canonical identity'; END IF;
       RETURN v_principal;
    END IF;
    INSERT INTO public.cikgulaju_web_principals(google_login_email)
    VALUES (p_verified_email) RETURNING id INTO v_principal;
    INSERT INTO public.cikgulaju_web_google_identities(auth_subject,principal_id)
    VALUES (p_auth_subject,v_principal);
    RETURN v_principal;
END;
$body$;

REVOKE ALL ON FUNCTION public.ensure_native_google_web_principal(uuid,text)
    FROM PUBLIC,anon,authenticated;
GRANT EXECUTE ON FUNCTION public.ensure_native_google_web_principal(uuid,text)
    TO service_role;

ALTER TABLE public.cikgulaju_web_principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cikgulaju_web_google_identities ENABLE ROW LEVEL SECURITY;

-- Backend-only. Browser session proves identity to server; the backend maps
-- to UUID and chooses the true credit source (Google-only vs legacy Telegram).
REVOKE ALL ON public.cikgulaju_web_principals,
    public.cikgulaju_web_google_identities FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_principals
    TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_google_identities
    TO service_role;

COMMENT ON TABLE public.cikgulaju_web_principals IS
    'DRAFT: canonical Web principal. Telegram legacy trial, subscription, and lifetime records are authoritative for linked users. No automatic email matching.';
COMMENT ON TABLE public.cikgulaju_web_google_identities IS
    'DRAFT: verified Google provider subject -> one UUID principal. Dual verified sessions and a review-gated link function are required before reassigning an identity.';
COMMIT;
)
    ),
    CONSTRAINT no_duplicate_legacy_trial_allowance CHECK (
        (legacy_telegram_user_id IS NULL
         AND google_only_trial_remaining BETWEEN 0 AND 10)
        OR (legacy_telegram_user_id IS NOT NULL
            AND google_only_trial_remaining IS NULL)
    )
);

-- Google subject UUID must be independently verified against the *production*
-- Supabase Auth user and provider = google, never browser-provided email/name.
-- Staging project Auth UUIDs are not automatically portable across projects.
CREATE TABLE IF NOT EXISTS public.cikgulaju_web_google_identities (
    auth_subject uuid PRIMARY KEY,
    principal_id uuid NOT NULL UNIQUE
       REFERENCES public.cikgulaju_web_principals(id) ON DELETE RESTRICT,
    verified_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.cikgulaju_web_principals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.cikgulaju_web_google_identities ENABLE ROW LEVEL SECURITY;

-- Backend-only. Browser session proves identity to server; the backend maps
-- to UUID and chooses the true credit source (Google-only vs legacy Telegram).
REVOKE ALL ON public.cikgulaju_web_principals,
    public.cikgulaju_web_google_identities FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_principals
    TO service_role;
GRANT SELECT, INSERT, UPDATE ON public.cikgulaju_web_google_identities
    TO service_role;

COMMENT ON TABLE public.cikgulaju_web_principals IS
    'DRAFT: canonical Web principal. Telegram legacy trial, subscription, and lifetime records are authoritative for linked users. No automatic email matching.';
COMMENT ON TABLE public.cikgulaju_web_google_identities IS
    'DRAFT: verified Google provider subject -> one UUID principal. Dual verified sessions and a review-gated link function are required before reassigning an identity.';
COMMIT;
