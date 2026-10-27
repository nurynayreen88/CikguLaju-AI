-- STAGING DESIGN ONLY: do not apply until authorization and calendar validation are reviewed.
-- Requires rph_taught_progress and rph_taught_events from 001.
-- This function is intentionally NOT SECURITY DEFINER. Call it only via a trusted
-- server-side DB connection after verifying teacher ownership, session and calendar.
-- Do not expose EXECUTE to anon/authenticated/public.
create or replace function public.confirm_taught_lesson_internal(
  p_teacher_id bigint,
  p_school_year integer,
  p_class_key text,
  p_subject_key text,
  p_session_instance_id text,
  p_session_date date,
  p_lesson_sequence integer,
  p_lesson_total integer,
  p_calendar_verified boolean,
  p_session_verified boolean
) returns text
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_current integer;
begin
  if p_teacher_id is null or p_school_year is null
     or p_school_year < 2020 or p_school_year > 2100
     or p_class_key is null or length(btrim(p_class_key)) = 0
     or p_subject_key is null or length(btrim(p_subject_key)) = 0
     or p_session_instance_id is null or length(btrim(p_session_instance_id)) = 0
     or p_session_date is null or extract(year from p_session_date)::integer <> p_school_year
     or p_lesson_sequence is null or p_lesson_total is null
     or p_lesson_total < 1 or p_lesson_sequence < 1 or p_lesson_sequence > p_lesson_total
     or p_calendar_verified is distinct from true
     or p_session_verified is distinct from true then
    raise exception 'invalid or unverified confirmation';
  end if;

  -- The progress row is the lock target. Concurrent callers serialize here.
  insert into public.rph_taught_progress
    (telegram_user_id, school_year, class_key, subject_key, last_confirmed_sequence)
  values (p_teacher_id, p_school_year, p_class_key, p_subject_key, 0)
  on conflict (telegram_user_id, school_year, class_key, subject_key) do nothing;

  select last_confirmed_sequence into v_current
    from public.rph_taught_progress
   where telegram_user_id = p_teacher_id and school_year = p_school_year
     and class_key = p_class_key and subject_key = p_subject_key
   for update;

  if v_current is null then
    raise exception 'progress row missing';
  end if;

  -- Replaying the exact same event is idempotent. Do not treat another
  -- session claiming an already-confirmed lesson as an acceptable replay.
  if exists (
    select 1 from public.rph_taught_events
     where telegram_user_id = p_teacher_id and school_year = p_school_year
       and class_key = p_class_key and subject_key = p_subject_key
       and session_instance_id = p_session_instance_id
       and session_date = p_session_date
       and lesson_sequence = p_lesson_sequence
  ) then
    return 'already_confirmed';
  end if;

  if p_lesson_sequence <> v_current + 1 then
    raise exception 'out-of-order lesson confirmation';
  end if;

  insert into public.rph_taught_events
    (telegram_user_id, school_year, class_key, subject_key,
     session_instance_id, session_date, lesson_sequence)
  values (p_teacher_id, p_school_year, p_class_key, p_subject_key,
          p_session_instance_id, p_session_date, p_lesson_sequence);

  update public.rph_taught_progress
     set last_confirmed_sequence = p_lesson_sequence,
         version = version + 1, updated_at = now()
   where telegram_user_id = p_teacher_id and school_year = p_school_year
     and class_key = p_class_key and subject_key = p_subject_key
     and last_confirmed_sequence = v_current;
  if not found then
    raise exception 'concurrent progress change';
  end if;
  return 'confirmed';
end;
$$;
-- Explicitly revoke default PUBLIC execute. No grants until trusted caller audited.
revoke all on function public.confirm_taught_lesson_internal(
 bigint, integer, text, text, text, date, integer, integer, boolean, boolean
) from public, anon, authenticated;
-- WARNING: server-side callers must not pass user-controlled verification flags
-- as trusted facts. A separate verified session/calendar source is required.
