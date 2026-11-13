-- Affiliate rewards and manual TNG eWallet payouts share the referral ledger.
-- Activate enrollment only after the Web and Telegram deployments are verified.
BEGIN;
ALTER TABLE public.referral_reward_settings
    ADD COLUMN affiliate_claims_enabled boolean NOT NULL DEFAULT false;
ALTER TABLE public.referral_point_events
    ADD COLUMN reward_percent numeric(5,2) CHECK (reward_percent > 0 AND reward_percent <= 100);

CREATE FUNCTION public.affiliate_record_reward_rate()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
    SELECT reward_percent INTO NEW.reward_percent FROM public.referral_reward_settings WHERE id=1;
    RETURN NEW;
END $$;
CREATE TRIGGER affiliate_reward_rate_at_award BEFORE INSERT ON public.referral_point_events
FOR EACH ROW EXECUTE FUNCTION public.affiliate_record_reward_rate();

CREATE TABLE public.affiliate_wallets (
    user_id bigint PRIMARY KEY REFERENCES public.referral_members(referrer_user_id),
    phone text NOT NULL CHECK (phone ~ '^01[0-9]{8,9}$'),
    confirmed_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.affiliate_claims (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id bigint NOT NULL REFERENCES public.referral_members(referrer_user_id),
    request_key uuid NOT NULL,
    points numeric(12,2) NOT NULL CHECK (points >= 10),
    phone_snapshot text NOT NULL CHECK (phone_snapshot ~ '^01[0-9]{8,9}$'),
    status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','processing','paid','rejected')),
    requested_at timestamptz NOT NULL DEFAULT now(),
    reviewer_id bigint,
    reviewed_at timestamptz,
    payment_reference text UNIQUE,
    paid_at timestamptz,
    rejection_reason text,
    UNIQUE (user_id, request_key),
    CHECK ((status = 'paid') = (payment_reference IS NOT NULL AND paid_at IS NOT NULL)),
    CHECK ((status = 'rejected') = (rejection_reason IS NOT NULL)),
    CHECK ((status = 'pending') = (reviewer_id IS NULL AND reviewed_at IS NULL))
);
CREATE INDEX affiliate_claims_user_history ON public.affiliate_claims(user_id, requested_at DESC, id DESC);
CREATE INDEX affiliate_claims_admin_queue ON public.affiliate_claims(status, requested_at DESC, id DESC);
CREATE TABLE public.affiliate_claim_events (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    claim_id uuid NOT NULL REFERENCES public.affiliate_claims(id),
    actor_id bigint NOT NULL CHECK (actor_id > 0),
    status text NOT NULL CHECK (status IN ('pending','processing','paid','rejected')),
    created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE public.affiliate_claim_proofs (
    claim_id uuid PRIMARY KEY REFERENCES public.affiliate_claims(id),
    content_type text NOT NULL CHECK (content_type IN ('image/png','image/jpeg','application/pdf')),
    content bytea NOT NULL CHECK (octet_length(content) BETWEEN 1 AND 2097152)
);
CREATE TABLE public.affiliate_point_reversals (
    event_id bigint PRIMARY KEY REFERENCES public.referral_point_events(id),
    source text NOT NULL CHECK (source IN ('pioneer_revoked','subscription_reversed')),
    reversed_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE public.affiliate_wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_claims ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_claim_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_claim_proofs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.affiliate_point_reversals ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.affiliate_wallets, public.affiliate_claims, public.affiliate_claim_events,
    public.affiliate_claim_proofs, public.affiliate_point_reversals FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.affiliate_wallets, public.affiliate_claims TO service_role;
GRANT SELECT, INSERT ON public.affiliate_claim_events, public.affiliate_claim_proofs,
    public.affiliate_point_reversals TO service_role;

CREATE FUNCTION public.affiliate_save_wallet(p_user bigint, p_phone text)
RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE member public.referral_members%ROWTYPE;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.referral_reward_settings WHERE id=1 AND affiliate_claims_enabled) THEN
        RETURN jsonb_build_object('error','closed');
    END IF;
    IF p_phone IS NULL OR p_phone !~ '^01[0-9]{8,9}$' OR NOT EXISTS (
        SELECT 1 FROM public.cikgulaju_users WHERE telegram_user_id=p_user
    ) THEN
        RETURN jsonb_build_object('error','invalid');
    END IF;
    INSERT INTO public.referral_members(referrer_user_id, referral_code)
    VALUES (p_user, replace(gen_random_uuid()::text,'-','')) ON CONFLICT (referrer_user_id) DO NOTHING;
    SELECT * INTO member FROM public.referral_members WHERE referrer_user_id=p_user FOR UPDATE;
    IF NOT member.enabled THEN RETURN jsonb_build_object('error','disabled'); END IF;
    INSERT INTO public.affiliate_wallets(user_id, phone) VALUES (p_user,p_phone)
    ON CONFLICT (user_id) DO UPDATE SET phone=excluded.phone,confirmed_at=now();
    RETURN jsonb_build_object('saved',true);
END $$;

CREATE FUNCTION public.affiliate_balance(p_user bigint)
RETURNS numeric LANGUAGE sql STABLE SECURITY INVOKER SET search_path = '' AS $$
    SELECT coalesce((SELECT sum(e.points_delta) FROM public.referral_point_events e
                      WHERE e.referrer_user_id=p_user AND NOT EXISTS (
                          SELECT 1 FROM public.affiliate_point_reversals r WHERE r.event_id=e.id)),0)
         - coalesce((SELECT sum(c.points) FROM public.affiliate_claims c
                      WHERE c.user_id=p_user AND c.status IN ('pending','processing','paid')),0);
$$;

CREATE FUNCTION public.affiliate_overview(p_user bigint)
RETURNS jsonb LANGUAGE plpgsql STABLE SECURITY INVOKER SET search_path = '' AS $$
DECLARE open_for_claims boolean;
DECLARE rate numeric;
BEGIN
    SELECT affiliate_claims_enabled, reward_percent INTO open_for_claims, rate
    FROM public.referral_reward_settings WHERE id=1;
    IF open_for_claims IS DISTINCT FROM true OR NOT EXISTS (
        SELECT 1 FROM public.cikgulaju_users WHERE telegram_user_id=p_user
    ) THEN RETURN jsonb_build_object('open',false); END IF;
    RETURN jsonb_build_object(
        'open',true,'rate',rate,
        'phone',(SELECT phone FROM public.affiliate_wallets WHERE user_id=p_user),
        'available',greatest(public.affiliate_balance(p_user),0)::text,
        'claims',coalesce((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.requested_at DESC, c.id DESC) FROM (
            SELECT id,points,status,requested_at,paid_at,payment_reference,rejection_reason
            FROM public.affiliate_claims WHERE user_id=p_user ORDER BY requested_at DESC,id DESC LIMIT 50
        ) c),'[]'::jsonb));
END $$;

CREATE FUNCTION public.affiliate_submit_claim(p_user bigint, p_points numeric, p_phone text, p_key uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE member public.referral_members%ROWTYPE;
DECLARE claim public.affiliate_claims%ROWTYPE;
DECLARE wallet text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.referral_reward_settings WHERE id=1 AND affiliate_claims_enabled) THEN
        RETURN jsonb_build_object('error','closed');
    END IF;
    IF p_key IS NULL OR p_points IS NULL OR NOT (p_points BETWEEN 10 AND 9999999999.99)
       OR round(p_points,2) <> p_points OR p_phone IS NULL OR p_phone !~ '^01[0-9]{8,9}$' THEN
        RETURN jsonb_build_object('error','invalid');
    END IF;
    -- The member row is the lock for wallet changes, reservations and reviews.
    SELECT * INTO member FROM public.referral_members WHERE referrer_user_id=p_user FOR UPDATE;
    IF NOT FOUND OR NOT member.enabled THEN RETURN jsonb_build_object('error','disabled'); END IF;
    SELECT * INTO claim FROM public.affiliate_claims WHERE user_id=p_user AND request_key=p_key;
    IF FOUND THEN
        IF claim.points <> p_points OR claim.phone_snapshot <> p_phone THEN
            RETURN jsonb_build_object('error','request_conflict');
        END IF;
        RETURN jsonb_build_object('id',claim.id,'status',claim.status,'replayed',true);
    END IF;
    SELECT phone INTO wallet FROM public.affiliate_wallets WHERE user_id=p_user;
    IF wallet IS DISTINCT FROM p_phone THEN RETURN jsonb_build_object('error','wallet_changed'); END IF;
    IF public.affiliate_balance(p_user) < p_points THEN RETURN jsonb_build_object('error','balance'); END IF;
    INSERT INTO public.affiliate_claims(user_id,request_key,points,phone_snapshot)
    VALUES (p_user,p_key,p_points,wallet) RETURNING * INTO claim;
    INSERT INTO public.affiliate_claim_events(claim_id,actor_id,status) VALUES (claim.id,p_user,'pending');
    RETURN jsonb_build_object('id',claim.id,'status',claim.status,'replayed',false);
END $$;

CREATE FUNCTION public.affiliate_review_claim(
    p_claim uuid, p_admin bigint, p_action text, p_reference text, p_reason text,
    p_content_type text, p_proof bytea
) RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE claim public.affiliate_claims%ROWTYPE;
DECLARE owner_id bigint;
BEGIN
    IF p_admin IS NULL OR p_admin <= 0 OR p_action IS NULL OR p_action NOT IN ('processing','paid','rejected') THEN
        RETURN jsonb_build_object('error','invalid');
    END IF;
    SELECT user_id INTO owner_id FROM public.affiliate_claims WHERE id=p_claim;
    IF NOT FOUND THEN RETURN jsonb_build_object('error','missing'); END IF;
    PERFORM 1 FROM public.referral_members WHERE referrer_user_id=owner_id FOR UPDATE;
    SELECT * INTO claim FROM public.affiliate_claims WHERE id=p_claim FOR UPDATE;
    IF claim.status = p_action AND claim.reviewer_id=p_admin
        AND (p_action <> 'paid' OR claim.payment_reference=p_reference)
        AND (p_action <> 'rejected' OR claim.rejection_reason=p_reason) THEN
        RETURN jsonb_build_object('status',claim.status);
    END IF;
    IF claim.status IN ('paid','rejected') OR (claim.status='processing' AND claim.reviewer_id<>p_admin)
       OR (p_action='paid' AND claim.status<>'processing') OR (p_action='processing' AND claim.status<>'pending') THEN
        RETURN jsonb_build_object('error','status');
    END IF;
    IF p_action='processing' AND (public.affiliate_balance(owner_id) < 0 OR NOT EXISTS (
        SELECT 1 FROM public.referral_members WHERE referrer_user_id=owner_id AND enabled
    )) THEN
        RETURN jsonb_build_object('error','balance');
    END IF;
    IF p_action='paid' THEN
        IF p_reference IS NULL OR p_reference !~ '^[A-Z0-9][A-Z0-9 ./_-]{2,79}$'
           OR p_content_type IS NULL OR p_content_type NOT IN ('image/png','image/jpeg','application/pdf')
           OR p_proof IS NULL OR octet_length(p_proof) NOT BETWEEN 1 AND 2097152 THEN
            RETURN jsonb_build_object('error','invalid');
        END IF;
        -- Uniqueness also covers concurrent reviews of different affiliates.
        BEGIN
            UPDATE public.affiliate_claims SET status='paid', payment_reference=p_reference, paid_at=now()
            WHERE id=p_claim;
            INSERT INTO public.affiliate_claim_proofs(claim_id,content_type,content)
            VALUES (p_claim,p_content_type,p_proof);
        EXCEPTION WHEN unique_violation THEN
            RETURN jsonb_build_object('error','reference_used');
        END;
    ELSIF p_action='rejected' THEN
        IF p_reason IS NULL OR length(btrim(p_reason)) NOT BETWEEN 3 AND 500 THEN
            RETURN jsonb_build_object('error','invalid');
        END IF;
        UPDATE public.affiliate_claims SET status='rejected', reviewer_id=p_admin,
            reviewed_at=now(), rejection_reason=p_reason WHERE id=p_claim;
    ELSE
        UPDATE public.affiliate_claims SET status='processing', reviewer_id=p_admin,
            reviewed_at=now() WHERE id=p_claim;
    END IF;
    INSERT INTO public.affiliate_claim_events(claim_id,actor_id,status) VALUES (p_claim,p_admin,p_action);
    RETURN jsonb_build_object('status',p_action);
END $$;

CREATE FUNCTION public.affiliate_reverse_paid_points()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE kind text;
DECLARE event_id bigint;
DECLARE referrer bigint;
DECLARE reason text;
BEGIN
    IF TG_TABLE_NAME='pioneer_entitlements' THEN
        IF OLD.revoked_at IS NOT NULL OR NEW.revoked_at IS NULL THEN RETURN NEW; END IF;
        kind := 'pioneer'; reason := 'pioneer_revoked';
    ELSE
        IF OLD.status NOT IN ('paid','approved') OR NEW.status NOT IN ('refunded','reversed','chargeback','cancelled','revoked') THEN
            RETURN NEW;
        END IF;
        kind := 'subscription'; reason := 'subscription_reversed';
    END IF;
    SELECT e.id,e.referrer_user_id INTO event_id,referrer FROM public.referral_point_events e
    WHERE e.payment_kind=kind AND e.payment_reference=OLD.payment_reference
      AND e.referred_user_id=OLD.telegram_user_id;
    IF FOUND THEN
        PERFORM 1 FROM public.referral_members WHERE referrer_user_id=referrer FOR UPDATE;
        INSERT INTO public.affiliate_point_reversals VALUES (event_id,reason,now()) ON CONFLICT DO NOTHING;
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER affiliate_pioneer_revoked AFTER UPDATE OF revoked_at ON public.pioneer_entitlements
FOR EACH ROW EXECUTE FUNCTION public.affiliate_reverse_paid_points();
CREATE TRIGGER affiliate_subscription_reversed AFTER UPDATE OF status ON public.subscription_payments
FOR EACH ROW EXECUTE FUNCTION public.affiliate_reverse_paid_points();

REVOKE ALL ON FUNCTION public.affiliate_save_wallet(bigint,text), public.affiliate_balance(bigint),
    public.affiliate_overview(bigint), public.affiliate_submit_claim(bigint,numeric,text,uuid),
    public.affiliate_review_claim(uuid,bigint,text,text,text,text,bytea),
    public.affiliate_reverse_paid_points(), public.affiliate_record_reward_rate() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.affiliate_save_wallet(bigint,text), public.affiliate_balance(bigint),
    public.affiliate_overview(bigint), public.affiliate_submit_claim(bigint,numeric,text,uuid),
    public.affiliate_review_claim(uuid,bigint,text,text,text,text,bytea),
    public.affiliate_reverse_paid_points(), public.affiliate_record_reward_rate() TO service_role;
COMMIT;
