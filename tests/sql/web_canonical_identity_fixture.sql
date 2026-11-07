-- Disposable PostgreSQL test fixture only; matches the production
-- legacy Telegram primary key and trial_remaining contract as audited.
-- The real production table must NEVER be created or modified by this test.
CREATE TABLE public.cikgulaju_users (
    telegram_user_id bigint PRIMARY KEY,
    credits integer NOT NULL DEFAULT 0 CHECK (credits >= 0),
    trial_remaining integer NOT NULL DEFAULT 10
        CHECK (trial_remaining >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    updated_at timestamptz NOT NULL DEFAULT now()
);
