-- DESIGN PROPOSAL ONLY: DO NOT APPLY TO STAGING OR PRODUCTION.
-- New canonical Google-first + existing Telegram account identity scaffold.
-- Verified against READ-ONLY 2026-11-07 metadata of production public.cikgulaju_users:
-- telegram_user_id bigint PRIMARY KEY, trial_remaining integer NOT NULL.
-- No BACKFILL, legacy ALTER, quota copy, entitlement overwrite or default signup.
-- Requires reviewed snapshot, identity link RPC, native generator, RLS/rollback plan.
BEGIN;

CREATE TABLE IF NOT EXISTS public.cikgulaju_web_principals (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    legacy_telegram_user_id bigint UNIQUE
        REFERENCES public.cikgulaju_users(telegram_user_id) ON DELETE RESTRICT,
    -- ONLY for Google-only principals. Linked legacy users use the original
    -- cikgulaju_users.trial_remaining instead, so a second ten credits cannot
    -- appear when a Google identity is explicitly linked to Telegram.
    google_only_trial_remaining integer DEFAULT 10,
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now(),
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
