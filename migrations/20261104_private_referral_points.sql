-- Private referral points (DRAFT). Additive tables only.
-- Apply in staging after validating 20% policy; NO backfill, no changes to
-- existing subscriptions, RPH credits, trials, or pioneer approval RPC.
-- Enabled only through a server-side CIKGULAJU_REFERRAL_POINTS_ENABLED flag.

CREATE TABLE IF NOT EXISTS public.referral_members (
    referrer_user_id bigint PRIMARY KEY REFERENCES public.cikgulaju_users(telegram_user_id),
    referral_code text NOT NULL UNIQUE
        CHECK (referral_code ~ '^[A-Za-z0-9_-]{16,48}$'),
    enabled boolean NOT NULL DEFAULT true,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.referral_signups (
    referred_user_id bigint PRIMARY KEY REFERENCES public.cikgulaju_users(telegram_user_id),
    referrer_user_id bigint NOT NULL REFERENCES public.referral_members(referrer_user_id),
    captured_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT no_self_referral CHECK (referred_user_id <> referrer_user_id)
);
CREATE INDEX IF NOT EXISTS idx_referral_signups_referrer
    ON public.referral_signups(referrer_user_id, captured_at DESC);

-- A single rate applies to ALL eligible verified payment values, not plan-specific points.
-- Remains disabled until staging checks and controlled launch.
CREATE TABLE IF NOT EXISTS public.referral_reward_settings (
    id smallint PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    reward_percent numeric(5,2) NOT NULL DEFAULT 20.00
        CHECK (reward_percent > 0 AND reward_percent <= 100),
    enabled boolean NOT NULL DEFAULT false
);
INSERT INTO public.referral_reward_settings (id,reward_percent,enabled)
VALUES (1,20.00,false) ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS public.referral_point_events (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    referrer_user_id bigint NOT NULL REFERENCES public.referral_members(referrer_user_id),
    referred_user_id bigint NOT NULL REFERENCES public.cikgulaju_users(telegram_user_id),
    payment_kind text NOT NULL CHECK (payment_kind IN ('pioneer','subscription')),
    payment_reference text NOT NULL,
    points_delta numeric(12,2) NOT NULL CHECK (points_delta > 0),
    awarded_at timestamptz NOT NULL DEFAULT now(),
    UNIQUE (payment_kind, payment_reference),
    UNIQUE (referred_user_id) -- default: only FIRST successful paid conversion
);
CREATE INDEX IF NOT EXISTS idx_referral_points_referrer
    ON public.referral_point_events(referrer_user_id, awarded_at DESC);

-- Never let browser / Telegram clients read or write other users' referral data.
ALTER TABLE public.referral_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_signups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_reward_settings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.referral_point_events ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.referral_members, public.referral_signups,
    public.referral_reward_settings, public.referral_point_events
    FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.referral_members,
    public.referral_signups, public.referral_reward_settings,
    public.referral_point_events TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.referral_point_events_id_seq TO service_role;

-- Only the trusted bot server (service role) may call these functions.
CREATE OR REPLACE FUNCTION public.referral_capture_signup(
    p_referred_user_id bigint, p_referral_code text
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE v_referrer bigint;
BEGIN
    IF p_referred_user_id IS NULL OR p_referred_user_id <= 0
       OR p_referral_code IS NULL OR length(p_referral_code) > 64 THEN
        RETURN jsonb_build_object('captured',false,'reason','invalid');
    END IF;
    SELECT referrer_user_id INTO v_referrer
    FROM public.referral_members
    WHERE referral_code=p_referral_code AND enabled IS TRUE;
    IF v_referrer IS NULL OR v_referrer=p_referred_user_id THEN
        RETURN jsonb_build_object('captured',false,'reason','invalid_referrer');
    END IF;
    -- Pre-existing users cannot claim a referral by reopening an invite link.
    IF NOT EXISTS (
        SELECT 1 FROM public.cikgulaju_users
        WHERE telegram_user_id=p_referred_user_id
        AND created_at >= now() - interval '15 minutes'
    ) THEN
        RETURN jsonb_build_object('captured',false,'reason','not_new_user');
    END IF;
    INSERT INTO public.referral_signups(referred_user_id,referrer_user_id)
    VALUES (p_referred_user_id,v_referrer)
    ON CONFLICT (referred_user_id) DO NOTHING;
    RETURN jsonb_build_object('captured',FOUND);
END;
$$;
REVOKE ALL ON FUNCTION public.referral_capture_signup(bigint,text)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.referral_capture_signup(bigint,text)
    TO service_role;

CREATE OR REPLACE FUNCTION public.referral_award_verified_payment(
    p_payer_user_id bigint, p_payment_kind text, p_payment_reference text
) RETURNS jsonb
LANGUAGE plpgsql
SECURITY INVOKER
SET search_path = ''
AS $$
DECLARE v_referrer bigint;
DECLARE v_capture timestamptz;
DECLARE v_amount numeric(12,2);
DECLARE v_percent numeric(5,2);
DECLARE v_points numeric(12,2);
DECLARE v_added bigint;
BEGIN
    IF p_payer_user_id IS NULL OR p_payer_user_id <= 0
       OR p_payment_kind NOT IN ('pioneer','subscription')
       OR nullif(btrim(p_payment_reference),'') IS NULL THEN
        RETURN jsonb_build_object('awarded',false,'reason','invalid');
    END IF;
    SELECT s.referrer_user_id,s.captured_at
      INTO v_referrer,v_capture
      FROM public.referral_signups s
      JOIN public.referral_members m
        ON m.referrer_user_id=s.referrer_user_id
     WHERE s.referred_user_id=p_payer_user_id
       AND m.enabled IS TRUE;
    IF v_referrer IS NULL THEN
        RETURN jsonb_build_object('awarded',false,'reason','no_referral');
    END IF;

    IF p_payment_kind='pioneer' THEN
        IF NOT EXISTS (
            SELECT 1 FROM public.pioneer_entitlements
            WHERE telegram_user_id=p_payer_user_id
              AND payment_reference=p_payment_reference
              AND entitlement='PIONEER_LIFETIME'
              AND approved_by > 0 AND revoked_at IS NULL
              AND approved_at >= v_capture
        ) THEN
            RETURN jsonb_build_object('awarded',false,'reason','not_verified');
        END IF;
        -- Verified Rakan Pembangun program has fixed RM10 payment.
        -- Do not infer unverified amounts from a receipt screenshot.
        v_amount := 10.00;
    ELSE
        SELECT amount_rm INTO v_amount
          FROM public.subscription_payments
         WHERE telegram_user_id=p_payer_user_id
           AND payment_reference=p_payment_reference
           AND status IN ('paid','approved')
           AND amount_rm > 0
           AND created_at >= v_capture
         LIMIT 1;
        IF v_amount IS NULL THEN
            RETURN jsonb_build_object('awarded',false,'reason','not_verified');
        END IF;
    END IF;

    SELECT reward_percent INTO v_percent
      FROM public.referral_reward_settings
     WHERE id = 1 AND enabled IS TRUE;
    IF v_percent IS NULL THEN
        RETURN jsonb_build_object('awarded',false,'reason','reward_disabled');
    END IF;
    -- Exact decimal arithmetic, rounded to two decimal point units.
    v_points := round(v_amount * v_percent / 100, 2);
    IF v_points <= 0 THEN
        RETURN jsonb_build_object('awarded',false,'reason','amount_too_small');
    END IF;
    INSERT INTO public.referral_point_events (
        referrer_user_id,referred_user_id,payment_kind,
        payment_reference,points_delta
    ) VALUES (
        v_referrer,p_payer_user_id,p_payment_kind,
        p_payment_reference,v_points
    ) ON CONFLICT DO NOTHING RETURNING id INTO v_added;
    RETURN jsonb_build_object(
        'awarded',v_added IS NOT NULL,
        'points',CASE WHEN v_added IS NULL THEN 0 ELSE v_points END,
        'reason',CASE WHEN v_added IS NULL THEN 'already_awarded' ELSE 'ok' END
    );
END;
$$;
REVOKE ALL ON FUNCTION public.referral_award_verified_payment(bigint,text,text)
    FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.referral_award_verified_payment(bigint,text,text)
    TO service_role;
