-- STAGING TEST DATABASE ONLY. Never execute against production.
-- Prerequisites: apply 001 and 002 on a disposable Postgres database.
-- Entire test is wrapped in a transaction and rolled back, including any data.
begin;
do $test$
declare
  v text;
  n integer;
  old_progress integer;
begin
  -- Synthetic user and class. Test starts with a fresh unique namespace.
  -- Test is self-contained even if rerun: rollback leaves no rows.
  v := public.confirm_taught_lesson_internal(
    -9223372036854775000, 2027, 'TEST_CLASS_A', 'TEST_EN',
    '2027-03-01/TEST_CLASS_A/TEST_EN/0800', date '2027-03-01',
    1, 160, true, true);
  if v <> 'confirmed' then raise exception 'first confirmation: %', v; end if;

  v := public.confirm_taught_lesson_internal(
    -9223372036854775000, 2027, 'TEST_CLASS_A', 'TEST_EN',
    '2027-03-01/TEST_CLASS_A/TEST_EN/0800', date '2027-03-01',
    1, 160, true, true);
  if v <> 'already_confirmed' then raise exception 'replay: %', v; end if;

  select count(*) into n from public.rph_taught_events
  where telegram_user_id = -9223372036854775000;
  if n <> 1 then raise exception 'duplicate event inserted'; end if;

  -- A different class starts at lesson 1 independently.
  v := public.confirm_taught_lesson_internal(
    -9223372036854775000, 2027, 'TEST_CLASS_B', 'TEST_EN',
    '2027-03-01/TEST_CLASS_B/TEST_EN/0900', date '2027-03-01',
    1, 160, true, true);
  if v <> 'confirmed' then raise exception 'class isolation'; end if;

  -- School-year rollover starts at lesson 1 without inheriting 2027 progress.
  v := public.confirm_taught_lesson_internal(
    -9223372036854775000, 2028, 'TEST_CLASS_A', 'TEST_EN',
    '2028-03-01/TEST_CLASS_A/TEST_EN/0800', date '2028-03-01',
    1, 160, true, true);
  if v <> 'confirmed' then raise exception 'year isolation'; end if;

  -- A failed confirmation must not modify progress.
  select last_confirmed_sequence into old_progress
  from public.rph_taught_progress
  where telegram_user_id = -9223372036854775000
    and school_year = 2027 and class_key = 'TEST_CLASS_A'
    and subject_key = 'TEST_EN';

  begin
    perform public.confirm_taught_lesson_internal(
      -9223372036854775000, 2027, 'TEST_CLASS_A', 'TEST_EN',
      '2027-03-02/TEST_CLASS_A/TEST_EN/0800', date '2027-03-02',
      3, 160, true, true);
    raise exception 'skip unexpectedly accepted';
  exception when others then
    if sqlerrm = 'skip unexpectedly accepted' then raise; end if;
  end;

  if (select last_confirmed_sequence from public.rph_taught_progress
      where telegram_user_id = -9223372036854775000
        and school_year = 2027 and class_key = 'TEST_CLASS_A'
        and subject_key = 'TEST_EN') <> old_progress then
    raise exception 'failed confirmation changed progress';
  end if;

  begin
    perform public.confirm_taught_lesson_internal(
      -9223372036854775000, 2027, 'TEST_CLASS_A', 'TEST_EN',
      '2027-03-02/TEST_CLASS_A/TEST_EN/0800', date '2027-03-02',
      2, 160, false, true);
    raise exception 'unverified calendar unexpectedly accepted';
  exception when others then
    if sqlerrm = 'unverified calendar unexpectedly accepted' then raise; end if;
  end;

  select count(*) into n from public.rph_taught_events
  where telegram_user_id = -9223372036854775000;
  if n <> 3 then raise exception 'expected three isolated events, got %', n; end if;
end;
$test$;
rollback;
