-- STAGING ONLY. DO NOT APPLY TO PRODUCTION WITHOUT REVIEW/BACKUP.
-- Separate taught progress from existing rph_progress (last generated RPH).
-- This script is additive, and deliberately does not grant API access.
create table if not exists public.rph_taught_progress (
  telegram_user_id bigint not null,
  school_year integer not null check (school_year between 2020 and 2100),
  class_key text not null check (length(trim(class_key)) > 0),
  subject_key text not null check (length(trim(subject_key)) > 0),
  last_confirmed_sequence integer not null default 0 check (last_confirmed_sequence >= 0),
  version bigint not null default 0,
  updated_at timestamptz not null default now(),
  primary key (telegram_user_id, school_year, class_key, subject_key)
);
create table if not exists public.rph_taught_events (
  event_id uuid primary key default gen_random_uuid(),
  telegram_user_id bigint not null,
  school_year integer not null,
  class_key text not null,
  subject_key text not null,
  session_instance_id text not null check (length(trim(session_instance_id)) > 0),
  session_date date not null,
  lesson_sequence integer not null check (lesson_sequence > 0),
  confirmed_at timestamptz not null default now(),
  foreign key (telegram_user_id, school_year, class_key, subject_key)
    references public.rph_taught_progress(telegram_user_id, school_year, class_key, subject_key),
  unique (telegram_user_id, school_year, class_key, subject_key, session_instance_id),
  unique (telegram_user_id, school_year, class_key, subject_key, lesson_sequence),
  check (extract(year from session_date)::integer = school_year)
);
create index if not exists idx_rph_taught_events_owner_time
  on public.rph_taught_events (telegram_user_id, school_year, confirmed_at desc);
alter table public.rph_taught_progress enable row level security;
alter table public.rph_taught_events enable row level security;
-- No policies or grants are added. Access is denied to anon/authenticated by default.
-- Server-side RPC and authorization design must be audited separately.
