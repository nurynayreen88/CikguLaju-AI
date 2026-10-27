-- STAGING REVIEW ONLY. Do not execute against production.
-- Additive mapping for stable class identity; legacy teacher_profiles remains unchanged.
-- Trusted backend must verify ownership and perform initial migration transactionally.
create table if not exists public.rph_class_identity (
  telegram_user_id bigint not null,
  school_year integer not null check (school_year between 2020 and 2100),
  class_id uuid not null,
  display_name text not null check (length(btrim(display_name)) > 0),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (telegram_user_id, school_year, class_id)
);
-- Prevent duplicate case-insensitive names within one teacher/year.
create unique index if not exists rph_class_identity_teacher_year_name_uq
on public.rph_class_identity
(telegram_user_id, school_year, lower(btrim(display_name)));
alter table public.rph_class_identity enable row level security;
revoke all on public.rph_class_identity from anon, authenticated;
-- Never drop or rewrite teacher_profiles.class_profiles or class_names.
-- No automatic backfill: ambiguous class names and timetable references
-- require explicit migration validation and rollback plan.
