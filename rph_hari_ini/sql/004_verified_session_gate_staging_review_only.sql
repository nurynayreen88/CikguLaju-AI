-- STAGING REVIEW ONLY. Not applied to production.
-- Hardened alternative to 002: caller cannot assert calendar/session verification.
-- Only a trusted backend can insert a verified eligibility record.
-- DO NOT grant insert/update/delete on this table to anon/authenticated.
create table if not exists public.rph_verified_sessions (
 telegram_user_id bigint not null,
 school_year integer not null check (school_year between 2020 and 2100),
 class_key text not null,
 subject_key text not null,
 session_instance_id text not null,
 session_date date not null,
 lesson_total integer not null check (lesson_total > 0),
 calendar_source text not null check (length(trim(calendar_source)) > 0),
 verified_at timestamptz not null default now(),
 primary key (telegram_user_id, school_year, class_key, subject_key, session_instance_id),
 check (extract(year from session_date)::integer = school_year)
);
alter table public.rph_verified_sessions enable row level security;
revoke all on public.rph_verified_sessions from anon, authenticated;

-- The verified session is a prerequisite, not a boolean supplied by the caller.
-- Authorization of teacher identity is a SERVER responsibility; this function
-- is not exposed to Telegram clients and is not SECURITY DEFINER.
create or replace function public.confirm_taught_lesson_verified_internal(
 p_teacher_id bigint, p_school_year integer, p_class_key text,
 p_subject_key text, p_session_instance_id text, p_lesson_sequence integer
) returns text
language plpgsql security invoker set search_path = ''
as $$
declare
 v_last integer;
 v_total integer;
 v_session_date date;
begin
 if p_teacher_id is null or p_school_year is null or
    p_class_key is null or length(btrim(p_class_key)) = 0 or
    p_subject_key is null or length(btrim(p_subject_key)) = 0 or
    p_session_instance_id is null or length(btrim(p_session_instance_id)) = 0 or
    p_lesson_sequence is null or p_lesson_sequence < 1 then
   raise exception 'invalid confirmation identity';
 end if;
 select lesson_total, session_date into v_total, v_session_date
 from public.rph_verified_sessions
 where telegram_user_id = p_teacher_id and school_year = p_school_year
   and class_key = p_class_key and subject_key = p_subject_key
   and session_instance_id = p_session_instance_id;
 if not found then raise exception 'session not independently verified'; end if;
 if p_lesson_sequence > v_total then raise exception 'lesson exceeds verified total'; end if;

 insert into public.rph_taught_progress
 (telegram_user_id, school_year, class_key, subject_key, last_confirmed_sequence)
 values (p_teacher_id, p_school_year, p_class_key, p_subject_key, 0)
 on conflict (telegram_user_id, school_year, class_key, subject_key) do nothing;

 select last_confirmed_sequence into v_last
 from public.rph_taught_progress
 where telegram_user_id = p_teacher_id and school_year = p_school_year
   and class_key = p_class_key and subject_key = p_subject_key
 for update;

 if exists (
   select 1 from public.rph_taught_events
   where telegram_user_id = p_teacher_id and school_year = p_school_year
     and class_key = p_class_key and subject_key = p_subject_key
     and session_instance_id = p_session_instance_id
     and session_date = v_session_date and lesson_sequence = p_lesson_sequence
 ) then return 'already_confirmed'; end if;
 if p_lesson_sequence <> v_last + 1 then raise exception 'non-sequential lesson'; end if;
 insert into public.rph_taught_events
 (telegram_user_id, school_year, class_key, subject_key,
  session_instance_id, session_date, lesson_sequence)
 values (p_teacher_id, p_school_year, p_class_key, p_subject_key,
         p_session_instance_id, v_session_date, p_lesson_sequence);
 update public.rph_taught_progress
 set last_confirmed_sequence = p_lesson_sequence, version = version + 1,
     updated_at = now()
 where telegram_user_id = p_teacher_id and school_year = p_school_year
   and class_key = p_class_key and subject_key = p_subject_key
   and last_confirmed_sequence = v_last;
 if not found then raise exception 'concurrent update'; end if;
 return 'confirmed';
end;
$$;
revoke all on function public.confirm_taught_lesson_verified_internal(
 bigint, integer, text, text, text, integer
) from public, anon, authenticated;
-- Pending: define verified session issuance using authenticated backend, approved
-- 2027 KPM calendar, teacher ownership, immutable timetable session identifiers.
-- This is a design candidate, NOT deployable until those gates exist.
