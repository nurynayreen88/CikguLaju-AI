-- Use the 12-digit DuitNow account number for TNG eWallet affiliate payouts.
BEGIN;
ALTER TABLE public.affiliate_wallets
    ALTER COLUMN phone DROP NOT NULL,
    ADD COLUMN account_number text CHECK (account_number ~ '^[0-9]{12}$'),
    ADD CONSTRAINT affiliate_wallet_destination CHECK ((phone IS NULL) <> (account_number IS NULL));
ALTER TABLE public.affiliate_claims
    ALTER COLUMN phone_snapshot DROP NOT NULL,
    ADD COLUMN account_number_snapshot text CHECK (account_number_snapshot ~ '^[0-9]{12}$'),
    ADD CONSTRAINT affiliate_claim_destination CHECK ((phone_snapshot IS NULL) <> (account_number_snapshot IS NULL));

-- Retire phone submissions from an older page or client. Historical destinations
-- stay with their claims. A claim already in processing can be reconciled.
CREATE OR REPLACE FUNCTION public.affiliate_save_wallet(p_user bigint, p_phone text)
RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path = '' AS $$
    SELECT jsonb_build_object('error','account_required');
$$;
CREATE OR REPLACE FUNCTION public.affiliate_submit_claim(p_user bigint,p_points numeric,p_phone text,p_key uuid)
RETURNS jsonb LANGUAGE sql SECURITY INVOKER SET search_path = '' AS $$
    SELECT jsonb_build_object('error','account_required');
$$;

CREATE FUNCTION public.affiliate_save_account(p_user bigint, p_account_number text)
RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE member public.referral_members%ROWTYPE;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.referral_reward_settings WHERE id=1 AND affiliate_claims_enabled) THEN
        RETURN jsonb_build_object('error','closed');
    END IF;
    IF p_account_number IS NULL OR p_account_number !~ '^[0-9]{12}$' OR NOT EXISTS (
        SELECT 1 FROM public.cikgulaju_users WHERE telegram_user_id=p_user
    ) THEN
        RETURN jsonb_build_object('error','invalid');
    END IF;
    INSERT INTO public.referral_members(referrer_user_id, referral_code)
    VALUES (p_user, replace(gen_random_uuid()::text,'-','')) ON CONFLICT (referrer_user_id) DO NOTHING;
    SELECT * INTO member FROM public.referral_members WHERE referrer_user_id=p_user FOR UPDATE;
    IF NOT member.enabled THEN RETURN jsonb_build_object('error','disabled'); END IF;
    INSERT INTO public.affiliate_wallets(user_id, account_number) VALUES (p_user,p_account_number)
    ON CONFLICT (user_id) DO UPDATE SET account_number=excluded.account_number, phone=NULL, confirmed_at=now();
    RETURN jsonb_build_object('saved',true);
END $$;

CREATE OR REPLACE FUNCTION public.affiliate_overview(p_user bigint)
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
        'account_number',(SELECT account_number FROM public.affiliate_wallets WHERE user_id=p_user),
        'available',greatest(public.affiliate_balance(p_user),0)::text,
        'claims',coalesce((SELECT jsonb_agg(to_jsonb(c) ORDER BY c.requested_at DESC, c.id DESC) FROM (
            SELECT id,points,status,requested_at,paid_at,payment_reference,rejection_reason
            FROM public.affiliate_claims WHERE user_id=p_user ORDER BY requested_at DESC,id DESC LIMIT 50
        ) c),'[]'::jsonb));
END $$;

CREATE FUNCTION public.affiliate_submit_account_claim(p_user bigint, p_points numeric, p_account_number text, p_key uuid)
RETURNS jsonb LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
DECLARE member public.referral_members%ROWTYPE;
DECLARE claim public.affiliate_claims%ROWTYPE;
DECLARE wallet text;
BEGIN
    IF NOT EXISTS (SELECT 1 FROM public.referral_reward_settings WHERE id=1 AND affiliate_claims_enabled) THEN
        RETURN jsonb_build_object('error','closed');
    END IF;
    IF p_key IS NULL OR p_points IS NULL OR NOT (p_points BETWEEN 10 AND 9999999999.99)
       OR round(p_points,2) <> p_points OR p_account_number IS NULL OR p_account_number !~ '^[0-9]{12}$' THEN
        RETURN jsonb_build_object('error','invalid');
    END IF;
    -- The member row is the lock for wallet changes, reservations and reviews.
    SELECT * INTO member FROM public.referral_members WHERE referrer_user_id=p_user FOR UPDATE;
    IF NOT FOUND OR NOT member.enabled THEN RETURN jsonb_build_object('error','disabled'); END IF;
    SELECT * INTO claim FROM public.affiliate_claims WHERE user_id=p_user AND request_key=p_key;
    IF FOUND THEN
        IF claim.points <> p_points OR claim.account_number_snapshot IS DISTINCT FROM p_account_number THEN
            RETURN jsonb_build_object('error','request_conflict');
        END IF;
        RETURN jsonb_build_object('id',claim.id,'status',claim.status,'replayed',true);
    END IF;
    SELECT account_number INTO wallet FROM public.affiliate_wallets WHERE user_id=p_user;
    IF wallet IS DISTINCT FROM p_account_number THEN RETURN jsonb_build_object('error','wallet_changed'); END IF;
    IF public.affiliate_balance(p_user) < p_points THEN RETURN jsonb_build_object('error','balance'); END IF;
    INSERT INTO public.affiliate_claims(user_id,request_key,points,account_number_snapshot)
    VALUES (p_user,p_key,p_points,wallet) RETURNING * INTO claim;
    INSERT INTO public.affiliate_claim_events(claim_id,actor_id,status) VALUES (claim.id,p_user,'pending');
    RETURN jsonb_build_object('id',claim.id,'status',claim.status,'replayed',false);
END $$;

CREATE OR REPLACE FUNCTION public.affiliate_review_claim(
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
    IF p_action='processing' AND claim.account_number_snapshot IS NULL THEN
        RETURN jsonb_build_object('error','account_required');
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

REVOKE ALL ON FUNCTION public.affiliate_save_account(bigint,text),
    public.affiliate_submit_account_claim(bigint,numeric,text,uuid) FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.affiliate_save_account(bigint,text),
    public.affiliate_submit_account_claim(bigint,numeric,text,uuid) TO service_role;
COMMIT;
