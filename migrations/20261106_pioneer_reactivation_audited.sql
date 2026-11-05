-- Reactivate a previously revoked Rakan Pembangun only after the same
-- authenticated Telegram admin explicitly verifies a new genuine RM10 payment.
-- The original entitlement remains present; its prior values are archived
-- atomically before the one-row-per-user entitlement is reactivated.
-- This migration DOES NOT approve any pending payment or reactivate any user.

create table if not exists public.pioneer_entitlement_reactivations (
  id bigint generated always as identity primary key,
  payment_request_id bigint not null unique
    references public.bot_payment_requests(id),
  telegram_user_id bigint not null,
  previous_payment_reference text not null,
  previous_approved_by bigint not null,
  previous_approved_at timestamptz not null,
  previous_revoked_by bigint,
  previous_revoked_at timestamptz not null,
  new_payment_reference text not null unique,
  reactivated_by bigint not null,
  reactivated_at timestamptz not null default now()
);
alter table public.pioneer_entitlement_reactivations enable row level security;
revoke all on table public.pioneer_entitlement_reactivations from public, anon, authenticated;
grant select, insert on table public.pioneer_entitlement_reactivations to service_role;

create or replace function public.reactivate_pioneer_after_revocation(
  p_telegram_user_id bigint,
  p_payment_reference text,
  p_approved_by bigint,
  p_payment_request_id bigint
)
returns jsonb
language plpgsql
security invoker
set search_path = ''
as $$
declare
  v_previous public.pioneer_entitlements%rowtype;
  v_reference text;
  v_active_count integer;
begin
  if p_telegram_user_id is null or p_telegram_user_id <= 0
      or p_approved_by is null or p_approved_by <= 0
      or p_payment_request_id is null or p_payment_request_id <= 0
      or nullif(btrim(p_payment_reference),'') is null then
    raise exception 'Invalid pioneer reactivation parameters';
  end if;
  v_reference := btrim(p_payment_reference);
  if length(v_reference) > 220 then
    raise exception 'Payment reference too long';
  end if;

  -- Lock consistently with the existing first-time approval RPC.
  perform pg_catalog.pg_advisory_xact_lock(20261026, 500);
  select * into v_previous
    from public.pioneer_entitlements
   where telegram_user_id = p_telegram_user_id
   for update;
  if not found or v_previous.revoked_at is null then
    raise exception 'Revoked pioneer entitlement required';
  end if;

  -- Bot manually verifies the actual bank transaction before invoking.
  -- DB independently requires a Pending, owner-matched, valid recorded proof.
  if not exists (
    select 1 from public.bot_payment_requests p
     where p.id = p_payment_request_id
       and p.chat_id = p_telegram_user_id::text
       and p.status = 'pending'
       and p.amount = 10.00
       and p.proof_received_at is not null
       and nullif(btrim(p.proof_telegram_file_id),'') is not null
       and p.notes in ('proof_received_web','proof_received_admin_notified')
  ) then
    raise exception 'Matching pending verified proof required';
  end if;

  -- Neither the original nor a previous reactivation reference may be reused.
  if exists(select 1 from public.pioneer_entitlements
             where payment_reference = v_reference)
     or exists(select 1 from public.pioneer_entitlement_reactivations
                where previous_payment_reference = v_reference
                   or new_payment_reference = v_reference) then
    raise exception 'Payment reference already used';
  end if;

  select public.pioneer_early_bird_count() into v_active_count;
  if v_active_count >= 500 then
    raise exception 'Pioneer quota full';
  end if;

  insert into public.pioneer_entitlement_reactivations (
    payment_request_id, telegram_user_id,
    previous_payment_reference, previous_approved_by,
    previous_approved_at, previous_revoked_by, previous_revoked_at,
    new_payment_reference, reactivated_by
  ) values (
    p_payment_request_id, p_telegram_user_id,
    v_previous.payment_reference, v_previous.approved_by,
    v_previous.approved_at, v_previous.revoked_by, v_previous.revoked_at,
    v_reference, p_approved_by
  );
  update public.pioneer_entitlements
     set payment_reference = v_reference,
         approved_by = p_approved_by,
         approved_at = now(),
         revoked_at = null,
         revoked_by = null
   where telegram_user_id = p_telegram_user_id
     and revoked_at = v_previous.revoked_at;
  if not found then
    raise exception 'Concurrent entitlement change';
  end if;
  return pg_catalog.jsonb_build_object(
      'approved', true, 'reactivated', true,
      'count', v_active_count + 1, 'remaining', 499 - v_active_count);
end;
$$;

revoke all on function public.reactivate_pioneer_after_revocation(bigint,text,bigint,bigint)
  from public, anon, authenticated;
grant execute on function public.reactivate_pioneer_after_revocation(bigint,text,bigint,bigint)
  to service_role;
