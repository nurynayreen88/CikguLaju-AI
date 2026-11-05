-- Additive, private delivery ledger for the one-time Web launch announcement.
-- No existing user/payment/referral/entitlement/credit records are changed.
-- This SQL must be applied before enabling the runtime broadcast bridge.
create table if not exists public.cikgulaju_broadcast_campaigns (
    campaign_id text primary key check (campaign_id ~ '^[a-z0-9_]{5,80}$'),
    confirmed_by bigint not null check (confirmed_by > 0),
    message_sha256 text not null check (message_sha256 ~ '^[a-f0-9]{64}$'),
    recipient_count integer not null check (recipient_count between 1 and 20000),
    confirmed_at timestamptz not null default now()
);
create table if not exists public.cikgulaju_broadcast_deliveries (
    campaign_id text not null references public.cikgulaju_broadcast_campaigns(campaign_id) on delete restrict,
    telegram_user_id bigint not null check (telegram_user_id > 0),
    status text not null default 'queued'
       check (status in ('queued', 'sending', 'sent', 'failed')),
    attempted_at timestamptz,
    finished_at timestamptz,
    error_code text check (length(error_code) <= 48),
    primary key (campaign_id, telegram_user_id)
);
create index if not exists cikgulaju_broadcast_deliveries_status_idx
    on public.cikgulaju_broadcast_deliveries (campaign_id, status);
alter table public.cikgulaju_broadcast_campaigns enable row level security;
alter table public.cikgulaju_broadcast_deliveries enable row level security;
revoke all on table public.cikgulaju_broadcast_campaigns from public, anon, authenticated;
revoke all on table public.cikgulaju_broadcast_deliveries from public, anon, authenticated;
grant select, insert on public.cikgulaju_broadcast_campaigns to service_role;
grant select, insert, update on public.cikgulaju_broadcast_deliveries to service_role;

-- Atomic one-time confirmation plus snapshot of registered users.
-- Fail before sending if any user count or transaction state changes.
create or replace function public.cikgulaju_broadcast_prepare(
    p_campaign text, p_admin bigint, p_sha256 text, p_expected_count integer
) returns integer
language plpgsql security invoker set search_path = ''
as $$
declare actual_count integer;
begin
    if p_campaign <> 'web_launch_20261106'
       or p_admin is null or p_admin <= 0
       or p_sha256 !~ '^[a-f0-9]{64}$'
       or p_expected_count is null or p_expected_count < 1
       or p_expected_count > 20000 then
        raise exception 'Invalid campaign confirmation';
    end if;
    insert into public.cikgulaju_broadcast_campaigns
        (campaign_id, confirmed_by, message_sha256, recipient_count)
    values (p_campaign, p_admin, p_sha256, p_expected_count);
    -- A repeated confirmation raises a unique violation. It never resends.
    insert into public.cikgulaju_broadcast_deliveries(campaign_id, telegram_user_id)
    select p_campaign, u.telegram_user_id
      from public.cikgulaju_users u
     where u.telegram_user_id > 0;
    get diagnostics actual_count = row_count;
    if actual_count <> p_expected_count then
        raise exception 'Registered recipients changed; preview again';
    end if;
    return actual_count;
end;
$$;
revoke all on function public.cikgulaju_broadcast_prepare(text,bigint,text,integer)
    from public, anon, authenticated;
grant execute on function public.cikgulaju_broadcast_prepare(text,bigint,text,integer)
    to service_role;

-- Two workers can safely run; only one can claim each queued recipient.
-- No automatic retry of a possibly delivered 'sending' row.
create or replace function public.cikgulaju_broadcast_claim(p_campaign text)
returns table (telegram_user_id bigint)
language sql security invoker set search_path = ''
as $$
    with candidate as (
        select d.campaign_id, d.telegram_user_id
        from public.cikgulaju_broadcast_deliveries d
        where d.campaign_id = p_campaign and d.status = 'queued'
        order by d.telegram_user_id
        for update skip locked
        limit 1
    )
    update public.cikgulaju_broadcast_deliveries d
    set status = 'sending', attempted_at = now()
    from candidate c
    where d.campaign_id = c.campaign_id
      and d.telegram_user_id = c.telegram_user_id
      and d.status = 'queued'
    returning d.telegram_user_id;
$$;
revoke all on function public.cikgulaju_broadcast_claim(text)
    from public, anon, authenticated;
grant execute on function public.cikgulaju_broadcast_claim(text)
    to service_role;
