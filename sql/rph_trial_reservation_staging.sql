-- Additive staging migration. DO NOT run against production before bot integration.
-- Existing trial balances and trial_ledger remain untouched.
begin;
create table if not exists public.rph_trial_reservations (
  request_id text primary key,
  telegram_user_id bigint not null references public.cikgulaju_users(telegram_user_id),
  status text not null default 'reserved' check (status in ('reserved','committed','released')),
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create index if not exists rph_trial_reservations_user_status_idx
  on public.rph_trial_reservations(telegram_user_id,status);
alter table public.rph_trial_reservations enable row level security;
revoke all on public.rph_trial_reservations from public, anon, authenticated;
grant select,insert,update on public.rph_trial_reservations to service_role;

create or replace function public.cikgulaju_reserve_rph_trial(p_telegram_user_id bigint,p_request_id text)
returns table(ok boolean, remaining integer, reservation_status text)
language plpgsql security invoker set search_path = ''
as $$
declare v_balance integer; v_active integer; v_row public.rph_trial_reservations%rowtype;
begin
  if p_request_id is null or length(p_request_id) < 8 or length(p_request_id) > 200 then
    raise exception 'Invalid reservation ID';
  end if;
  insert into public.cikgulaju_users(telegram_user_id,trial_remaining)
    values(p_telegram_user_id,5) on conflict(telegram_user_id) do nothing;
  select trial_remaining into v_balance from public.cikgulaju_users
    where telegram_user_id=p_telegram_user_id for update;
  select * into v_row from public.rph_trial_reservations where request_id=p_request_id;
  if found then
    if v_row.telegram_user_id <> p_telegram_user_id then raise exception 'Reservation owner mismatch'; end if;
    return query select (v_row.status in ('reserved','committed')),v_balance,v_row.status;
    return;
  end if;
  select count(*)::integer into v_active from public.rph_trial_reservations
    where telegram_user_id=p_telegram_user_id and status='reserved';
  if v_balance-v_active <= 0 then
    return query select false,v_balance,'unavailable'::text; return;
  end if;
  insert into public.rph_trial_reservations(request_id,telegram_user_id) values(p_request_id,p_telegram_user_id);
  return query select true,v_balance,'reserved'::text;
end $$;

create or replace function public.cikgulaju_commit_rph_trial(p_telegram_user_id bigint,p_request_id text)
returns table(ok boolean,remaining integer,reservation_status text)
language plpgsql security invoker set search_path=''
as $$
declare v_balance integer; v_row public.rph_trial_reservations%rowtype;
begin
  select trial_remaining into v_balance from public.cikgulaju_users
    where telegram_user_id=p_telegram_user_id for update;
  select * into v_row from public.rph_trial_reservations where request_id=p_request_id for update;
  if not found or v_row.telegram_user_id <> p_telegram_user_id then
    return query select false,coalesce(v_balance,0),'missing'::text; return;
  end if;
  if v_row.status='committed' then
    return query select true,v_balance,'committed'::text; return;
  end if;
  if v_row.status<>'reserved' then
    return query select false,v_balance,v_row.status; return;
  end if;
  if v_balance is null or v_balance<=0 then
    return query select false,coalesce(v_balance,0),'balance_unavailable'::text; return;
  end if;
  update public.cikgulaju_users set trial_remaining=trial_remaining-1,updated_at=now()
    where telegram_user_id=p_telegram_user_id returning trial_remaining into v_balance;
  update public.rph_trial_reservations set status='committed',updated_at=now() where request_id=p_request_id;
  insert into public.trial_ledger(telegram_user_id,amount,reason,reference_id,balance_after)
    values(p_telegram_user_id,-1,'successful_rph_delivery','rph-reservation:'||p_request_id,v_balance);
  return query select true,v_balance,'committed'::text;
end $$;

create or replace function public.cikgulaju_release_rph_trial(p_telegram_user_id bigint,p_request_id text)
returns table(ok boolean,reservation_status text)
language plpgsql security invoker set search_path=''
as $$
declare v_row public.rph_trial_reservations%rowtype; v_balance integer;
begin
  select trial_remaining into v_balance from public.cikgulaju_users
    where telegram_user_id=p_telegram_user_id for update;
  select * into v_row from public.rph_trial_reservations where request_id=p_request_id for update;
  if not found or v_row.telegram_user_id<>p_telegram_user_id then
    return query select false,'missing'::text; return;
  end if;
  if v_row.status='committed' then return query select false,'committed'::text; return; end if;
  if v_row.status='released' then return query select true,'released'::text; return; end if;
  update public.rph_trial_reservations set status='released',updated_at=now()
    where request_id=p_request_id and status='reserved';
  return query select true,'released'::text;
end $$;
revoke all on function public.cikgulaju_reserve_rph_trial(bigint,text) from public,anon,authenticated;
revoke all on function public.cikgulaju_commit_rph_trial(bigint,text) from public,anon,authenticated;
revoke all on function public.cikgulaju_release_rph_trial(bigint,text) from public,anon,authenticated;
grant execute on function public.cikgulaju_reserve_rph_trial(bigint,text) to service_role;
grant execute on function public.cikgulaju_commit_rph_trial(bigint,text) to service_role;
grant execute on function public.cikgulaju_release_rph_trial(bigint,text) to service_role;
commit;
