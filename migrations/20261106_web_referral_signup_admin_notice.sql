-- Applied to CikguLaju Supabase 2026-11-06.
-- Web referral admin notification dedupe, additive only.
CREATE TABLE IF NOT EXISTS public.web_referral_signup_notices (
    referred_user_id bigint PRIMARY KEY
        REFERENCES public.cikgulaju_users(telegram_user_id),
    created_at timestamptz NOT NULL DEFAULT now()
);
ALTER TABLE public.web_referral_signup_notices ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.web_referral_signup_notices FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT ON public.web_referral_signup_notices TO service_role;
