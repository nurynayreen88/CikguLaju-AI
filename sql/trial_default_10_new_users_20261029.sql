-- Apply once in Supabase SQL editor before deploying 10-trial application.
-- New users only; existing trial_remaining values are preserved.
ALTER TABLE public.cikgulaju_users ALTER COLUMN trial_remaining SET DEFAULT 10;
-- Existing balances and pioneer entitlements are intentionally untouched.
