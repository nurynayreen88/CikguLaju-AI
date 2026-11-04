-- Persistent Telegram receipt pointers for payment audit/review.
-- Only Telegram file identifiers; the original image/PDF stays with Telegram.
-- No existing payment rows are changed or deleted.
BEGIN;
ALTER TABLE public.bot_payment_requests
    ADD COLUMN IF NOT EXISTS proof_telegram_file_id text,
    ADD COLUMN IF NOT EXISTS proof_file_unique_id text,
    ADD COLUMN IF NOT EXISTS proof_telegram_message_id bigint,
    ADD COLUMN IF NOT EXISTS proof_mime_type text,
    ADD COLUMN IF NOT EXISTS proof_received_at timestamptz;
COMMIT;
