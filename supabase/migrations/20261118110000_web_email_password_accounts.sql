-- Email/password identities for the production Web login.
-- Existing Telegram IDs remain the canonical account key for linked teachers.
-- New email-only Web accounts receive reserved high bigint IDs so the current
-- trial, profile, payment, and subscription tables continue to use one key.
create sequence if not exists public.cikgulaju_web_email_account_seq
    as bigint
    start with 4000000000000000000
    increment by 1
    minvalue 4000000000000000000
    maxvalue 8999999999999999999
    no cycle;

create table if not exists public.web_email_identities (
    auth_user_id uuid primary key,
    email text not null unique,
    account_user_id bigint not null
        references public.cikgulaju_users(telegram_user_id) on delete restrict,
    status text not null default 'active'
        check (status = 'active'),
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    check (email = lower(btrim(email)))
);

create unique index if not exists web_email_identities_one_active_email_per_account
    on public.web_email_identities(account_user_id)
    where status = 'active';

alter table public.web_email_identities enable row level security;
revoke all on public.web_email_identities from public, anon, authenticated;
grant select, insert, update, delete on public.web_email_identities to service_role;
grant usage, select on sequence public.cikgulaju_web_email_account_seq to service_role;

create or replace function public.link_verified_web_email(
    p_auth_user_id uuid,
    p_email text,
    p_telegram_user_id bigint
) returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_email text := lower(btrim(p_email));
    v_row public.web_email_identities%rowtype;
begin
    if p_auth_user_id is null or p_telegram_user_id is null
       or p_telegram_user_id <= 0 or p_telegram_user_id >= 1000000000000000000
       or v_email is null or length(v_email) > 254
       or v_email !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' then
        raise exception 'invalid verified email link';
    end if;
    if not exists (select 1 from public.cikgulaju_users
                   where telegram_user_id = p_telegram_user_id) then
        raise exception 'telegram account not found';
    end if;

    select * into v_row from public.web_email_identities
      where auth_user_id = p_auth_user_id for update;
    if found then
        if v_row.email <> v_email or v_row.account_user_id <> p_telegram_user_id then
            raise exception 'email identity already belongs to another account';
        end if;
        return p_telegram_user_id;
    end if;

    select * into v_row from public.web_email_identities
      where email = v_email for update;
    if found then
        raise exception 'email already belongs to another account';
    end if;
    select * into v_row from public.web_email_identities
      where account_user_id = p_telegram_user_id and status = 'active' for update;
    if found then
        raise exception 'telegram account already has an email login';
    end if;

    insert into public.web_email_identities(auth_user_id, email, account_user_id, status)
      values (p_auth_user_id, v_email, p_telegram_user_id, 'active');
    return p_telegram_user_id;
end;
$$;

create or replace function public.ensure_web_email_account(
    p_auth_user_id uuid,
    p_email text
) returns bigint
language plpgsql
security definer
set search_path = public, pg_temp
as $$
declare
    v_email text := lower(btrim(p_email));
    v_row public.web_email_identities%rowtype;
    v_account_id bigint;
begin
    if p_auth_user_id is null or v_email is null or length(v_email) > 254
       or v_email !~ '^[^@[:space:]]+@[^@[:space:]]+\.[^@[:space:]]+$' then
        raise exception 'invalid verified email identity';
    end if;

    perform pg_advisory_xact_lock(hashtextextended(p_auth_user_id::text, 0));

    select * into v_row from public.web_email_identities
      where auth_user_id = p_auth_user_id for update;
    if found then
        if v_row.email <> v_email then
            raise exception 'verified email does not match account mapping';
        end if;
        return v_row.account_user_id;
    end if;

    select * into v_row from public.web_email_identities
      where email = v_email for update;
    if found then
        raise exception 'email already belongs to another authentication account';
    end if;

    v_account_id := nextval('public.cikgulaju_web_email_account_seq');
    insert into public.cikgulaju_users(
        telegram_user_id, username, first_name, credits, trial_remaining
    ) values (v_account_id, 'web-email', 'Cikgu', 0, 10);
    insert into public.teacher_profiles(telegram_user_id, display_name)
      values (v_account_id, 'Cikgu')
      on conflict (telegram_user_id) do nothing;
    insert into public.web_email_identities(auth_user_id, email, account_user_id, status)
      values (p_auth_user_id, v_email, v_account_id, 'active');
    return v_account_id;
end;
$$;

revoke all on function public.link_verified_web_email(uuid, text, bigint) from public, anon, authenticated;
revoke all on function public.ensure_web_email_account(uuid, text) from public, anon, authenticated;
grant execute on function public.link_verified_web_email(uuid, text, bigint) to service_role;
grant execute on function public.ensure_web_email_account(uuid, text) to service_role;
