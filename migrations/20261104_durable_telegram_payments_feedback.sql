-- CikguLaju: additive durable Telegram user data (2026-11-04).
-- Does NOT reset, modify or delete any existing user/profile/credit/entitlement data.
-- Service-role-only access. Do not expose these tables to anon/authenticated.
BEGIN;

CREATE TABLE IF NOT EXISTS public.bot_payment_requests (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chat_id text NOT NULL CHECK (chat_id ~ '^[0-9]+$'),
    amount numeric(10,2) NOT NULL CHECK (amount > 0),
    telegram_message_id bigint,
    status text NOT NULL DEFAULT 'pending'
        CHECK (status IN ('pending','approved','rejected')),
    submitted_at timestamptz NOT NULL DEFAULT now(),
    reviewed_at timestamptz,
    reviewed_by text NOT NULL DEFAULT '',
    notes text NOT NULL DEFAULT ''
);
-- Match old CikguLaju rule: one pending request per Telegram ID.
CREATE UNIQUE INDEX IF NOT EXISTS bot_payments_one_pending_per_user
    ON public.bot_payment_requests(chat_id) WHERE status='pending';
CREATE INDEX IF NOT EXISTS bot_payments_status_submitted
    ON public.bot_payment_requests(status, submitted_at DESC);

CREATE TABLE IF NOT EXISTS public.bot_user_feedback (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    chat_id text NOT NULL CHECK (chat_id ~ '^[0-9]+$'),
    category text NOT NULL DEFAULT 'Umum',
    feedback_text text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    status text NOT NULL DEFAULT 'baru'
        CHECK (status IN ('baru','dibaca','selesai'))
);
CREATE INDEX IF NOT EXISTS bot_feedback_status_created
    ON public.bot_user_feedback(status, created_at DESC);

ALTER TABLE public.bot_payment_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bot_user_feedback ENABLE ROW LEVEL SECURITY;
REVOKE ALL ON public.bot_payment_requests, public.bot_user_feedback
    FROM PUBLIC, anon, authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON
    public.bot_payment_requests, public.bot_user_feedback TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.bot_payment_requests_id_seq TO service_role;
GRANT USAGE, SELECT ON SEQUENCE public.bot_user_feedback_id_seq TO service_role;

-- Exact counts stay database-side; never truncate at PostgREST's row limit.
CREATE OR REPLACE FUNCTION public.bot_payment_status_counts()
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = ''
AS $body$
    SELECT jsonb_build_object(
        'pending', COUNT(*) FILTER(WHERE status='pending'),
        'approved', COUNT(*) FILTER(WHERE status='approved'),
        'rejected', COUNT(*) FILTER(WHERE status='rejected')
    ) FROM public.bot_payment_requests
$body$;
CREATE OR REPLACE FUNCTION public.bot_feedback_status_counts()
RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = ''
AS $body$
    SELECT jsonb_build_object(
        'baru', COUNT(*) FILTER(WHERE status='baru'),
        'dibaca', COUNT(*) FILTER(WHERE status='dibaca'),
        'selesai', COUNT(*) FILTER(WHERE status='selesai'),
        'total', COUNT(*)
    ) FROM public.bot_user_feedback
$body$;
REVOKE ALL ON FUNCTION public.bot_payment_status_counts() FROM PUBLIC, anon, authenticated;
REVOKE ALL ON FUNCTION public.bot_feedback_status_counts() FROM PUBLIC, anon, authenticated;
GRANT EXECUTE ON FUNCTION public.bot_payment_status_counts() TO service_role;
GRANT EXECUTE ON FUNCTION public.bot_feedback_status_counts() TO service_role;

COMMIT;
