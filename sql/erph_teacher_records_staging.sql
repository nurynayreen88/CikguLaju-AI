-- Staging migration; do not apply until reviewed and approved for production.
create table public.erph_teacher_records (
  id uuid primary key default gen_random_uuid(),
  owner_telegram_id bigint not null check (owner_telegram_id > 0),
  teaching_date date not null,
  class_name text not null check (char_length(class_name) between 1 and 80),
  subject_name text not null check (char_length(subject_name) between 1 and 120),
  start_time time not null,
  end_time time not null check (end_time > start_time),
  title text not null check (char_length(title) between 1 and 200),
  objectives text not null default '' check (char_length(objectives) <= 4000),
  activities text not null default '' check (char_length(activities) <= 12000),
  reflection text not null default '' check (char_length(reflection) <= 4000),
  rph_format text not null default 'biasa' check (rph_format in ('biasa','5p')),
  status text not null default 'draft' check (status in ('draft','saved','completed')),
  updated_at timestamptz not null default now(),
  unique (owner_telegram_id, teaching_date, class_name, start_time)
);
alter table public.erph_teacher_records enable row level security;
revoke all on public.erph_teacher_records from public, anon, authenticated;
grant select,insert,update on public.erph_teacher_records to service_role;
create index erph_teacher_records_owner_date on public.erph_teacher_records(owner_telegram_id, teaching_date);
