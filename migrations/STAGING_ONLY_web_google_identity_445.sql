-- Proposed additive migration for a DEDICATED staging Supabase database.
-- DO NOT run against production; requires DB snapshot, RLS review, and approval.
-- Legacy Telegram-keyed tables and balances remain untouched.

BEGIN;

CREATE TABLE IF NOT EXISTS public.web_accounts (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    legacy_telegram_user_id bigint UNIQUE
        REFERENCES public.cikgulaju_users(telegram_user_id) ON DELETE RESTRICT,
    google_trial_remaining integer NOT NULL DEFAULT 10
        CHECK (google_trial_remaining BETWEEN 0 AND 10),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.web_account_identities (
    provider text NOT NULL CHECK (provider IN ('google', 'telegram')),
    subject text NOT NULL CHECK (length(subject) BETWEEN 1 AND 128),
    account_id uuid NOT NULL REFERENCES public.web_accounts(id) ON DELETE CASCADE,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (provider, subject),
    UNIQUE (account_id, provider)
);

-- The authenticated browser must NEVER write identity/entitlement mappings.
ALTER TABLE public.web_accounts ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.web_account_identities ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON TABLE public.web_accounts FROM PUBLIC, anon, authenticated;
REVOKE ALL ON TABLE public.web_account_identities FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.web_accounts TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON TABLE public.web_account_identities TO service_role;

-- Called only by a server with the service role AFTER verifying the Google
-- identity via Supabase Auth. No email matching, fake Telegram IDs, or browser
-- parameters as proof of identity. The routine is transactionally idempotent.
CREATE OR REPLACE FUNCTION public.ensure_google_web_account(p_auth_subject uuid)
RETURNS uuid
LANGUAGE plpgsql SECURITY INVOKER
SET search_path = public, pg_temp
AS $function$
DECLARE
    existing_id uuid;
    candidate_id uuid;
    claimed_id uuid;
BEGIN
    IF p_auth_subject IS NULL THEN
        RAISE EXCEPTION 'verified Google identity required';
    END IF;

    SELECT account_id INTO existing_id
    FROM public.web_account_identities
    WHERE provider = 'google' AND subject = p_auth_subject::text;
    IF existing_id IS NOT NULL THEN
        RETURN existing_id;
    END IF;

    INSERT INTO public.web_accounts DEFAULT VALUES RETURNING id INTO candidate_id;
    INSERT INTO public.web_account_identities(provider, subject, account_id)
    VALUES ('google', p_auth_subject::text, candidate_id)
    ON CONFLICT (provider, subject) DO NOTHING
    RETURNING account_id INTO claimed_id;

    IF claimed_id IS NULL THEN
        -- A concurrent verified callback won the unique provider+subject race.
        DELETE FROM public.web_accounts WHERE id = candidate_id;
        SELECT account_id INTO claimed_id FROM public.web_account_identities
        WHERE provider = 'google' AND subject = p_auth_subject::text;
    END IF;
    IF claimed_id IS NULL THEN
        RAISE EXCEPTION 'google identity mapping not confirmed';
    END IF;
    RETURN claimed_id;
END;
$function$;

REVOKE ALL ON FUNCTION public.ensure_google_web_account(uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.ensure_google_web_account(uuid) TO service_role;

COMMIT;

-- DO NOT assign Google accounts privileges in legacy Telegram paths.
-- Google-only users require UUID-aware RPH trial debit RPC, independent Web
-- teacher profile/payment records and a reviewed legacy account linking flow.
-- Identity linking must verify Google and Telegram owners explicitly.
