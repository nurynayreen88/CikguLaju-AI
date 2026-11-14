-- Both admin panels use this transaction for proof-backed Rakan Pembangun decisions.
CREATE FUNCTION public.review_rakan_payment(
    p_payment_id bigint, p_payer bigint, p_admin bigint,
    p_proof_received_at timestamptz, p_decision text
) RETURNS jsonb
LANGUAGE plpgsql SECURITY INVOKER SET search_path = ''
AS $$
DECLARE
    payment public.bot_payment_requests%ROWTYPE;
    existing public.pioneer_entitlements%ROWTYPE;
    reference text;
    approved jsonb;
    reward jsonb;
BEGIN
    IF p_payment_id IS NULL OR p_payment_id <= 0 OR p_payer IS NULL OR p_payer <= 0
       OR p_admin IS NULL OR p_admin <= 0
       OR p_decision IS NULL OR p_decision NOT IN ('approved', 'rejected') THEN
        RETURN jsonb_build_object('error', 'invalid');
    END IF;

    SELECT * INTO payment FROM public.bot_payment_requests
    WHERE id = p_payment_id AND chat_id = p_payer::text FOR UPDATE;
    IF NOT FOUND THEN
        RETURN jsonb_build_object('error', 'missing');
    END IF;
    IF payment.status <> 'pending' THEN
        RETURN jsonb_build_object('error', 'reviewed');
    END IF;
    IF payment.amount NOT IN (10.00, 20.00) THEN
        RETURN jsonb_build_object('error', 'unsupported');
    END IF;
    IF payment.proof_received_at IS NULL
       OR payment.proof_received_at IS DISTINCT FROM p_proof_received_at
       OR nullif(btrim(payment.proof_telegram_file_id), '') IS NULL THEN
        RETURN jsonb_build_object('error', 'proof_changed');
    END IF;

    IF p_decision = 'approved' THEN
        PERFORM pg_advisory_xact_lock(20261026, 500);
        SELECT * INTO existing FROM public.pioneer_entitlements
        WHERE telegram_user_id = p_payer FOR UPDATE;
        IF FOUND AND existing.revoked_at IS NULL THEN
            RETURN jsonb_build_object('error', 'already_active');
        END IF;

        reference := 'rakan-payment:' || p_payment_id::text;
        IF existing.revoked_at IS NOT NULL THEN
            approved := public.reactivate_pioneer_after_revocation(
                p_payer, reference, p_admin, p_payment_id);
        ELSE
            approved := public.approve_pioneer_early_bird(p_payer, reference, p_admin);
        END IF;
        IF approved->>'approved' IS DISTINCT FROM 'true' THEN
            RAISE EXCEPTION 'Rakan payment approval was not confirmed';
        END IF;
    END IF;

    UPDATE public.bot_payment_requests
    SET status = p_decision, reviewed_at = now(), reviewed_by = p_admin::text,
        notes = CASE WHEN p_decision = 'approved'
            THEN 'Rakan Pembangun verified by admin' ELSE 'Rakan Pembangun rejected by admin' END
    WHERE id = p_payment_id;

    IF p_decision = 'approved' THEN
        reward := public.referral_award_verified_payment(p_payer, 'pioneer', reference);
    END IF;
    RETURN jsonb_build_object('status', p_decision, 'reward', reward);
END;
$$;

REVOKE ALL ON FUNCTION public.review_rakan_payment(bigint, bigint, bigint, timestamptz, text)
FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.review_rakan_payment(bigint, bigint, bigint, timestamptz, text)
TO service_role;
