-- Record the automatic enrollment already applied to CikguLaju production.
CREATE OR REPLACE FUNCTION public.ensure_cikgulaju_referral_member()
RETURNS trigger LANGUAGE plpgsql SECURITY INVOKER SET search_path = '' AS $$
BEGIN
    INSERT INTO public.referral_members (referrer_user_id, referral_code, enabled)
    VALUES (NEW.telegram_user_id, md5('cikgulaju-referral-v1:' || NEW.telegram_user_id::text), true)
    ON CONFLICT (referrer_user_id) DO NOTHING;
    RETURN NEW;
END;
$$;

CREATE TRIGGER cikgulaju_users_auto_referral
AFTER INSERT ON public.cikgulaju_users
FOR EACH ROW EXECUTE FUNCTION public.ensure_cikgulaju_referral_member();

INSERT INTO public.referral_members (referrer_user_id, referral_code, enabled)
SELECT telegram_user_id, md5('cikgulaju-referral-v1:' || telegram_user_id::text), true
FROM public.cikgulaju_users
WHERE telegram_user_id IS NOT NULL
ON CONFLICT (referrer_user_id) DO NOTHING;
