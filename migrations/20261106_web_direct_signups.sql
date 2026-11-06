-- Applied to CikguLaju Supabase (2026-11-06), additive and non-destructive.
-- Trusted direct Web signup marker and one-time admin-notification claim.
CREATE TABLE IF NOT EXISTS public.web_direct_signups (
  telegram_user_id bigint PRIMARY KEY REFERENCES public.cikgulaju_users(telegram_user_id),
  created_at timestamptz NOT NULL DEFAULT now(),
  notified_at timestamptz
);
ALTER TABLE public.web_direct_signups ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.web_direct_signups FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE ON public.web_direct_signups TO service_role;
