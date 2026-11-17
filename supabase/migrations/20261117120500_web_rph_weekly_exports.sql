begin;

create table public.web_rph_weekly_exports (
    teacher_id bigint not null check (teacher_id > 0),
    week_start date not null check (extract(isodow from week_start) = 1),
    exports jsonb not null default '{}'::jsonb check (jsonb_typeof(exports) = 'object'),
    primary key (teacher_id, week_start)
);

alter table public.web_rph_weekly_exports enable row level security;
revoke all on public.web_rph_weekly_exports from public, anon, authenticated, service_role;
grant select, insert, update on public.web_rph_weekly_exports to service_role;

create function public.web_rph_weekly_usage(
    p_teacher_id bigint,
    p_export_id uuid default null,
    p_content_hash text default null
)
returns table (allowed boolean, remaining integer, usage_week_start date)
language plpgsql security invoker set search_path = ''
as $$
declare
    starts date := date_trunc('week', statement_timestamp() at time zone 'Asia/Kuala_Lumpur')::date;
    saved jsonb;
    export_count integer;
    existing_hash text;
begin
    if p_teacher_id is null or p_teacher_id <= 0
        or (p_export_id is null) <> (p_content_hash is null)
        or (p_content_hash is not null and p_content_hash !~ '^[0-9a-f]{64}$') then
        raise exception 'Invalid weekly export' using errcode = '22023';
    end if;

    if p_export_id is null then
        select e.exports into saved
        from public.web_rph_weekly_exports as e
        where e.teacher_id = p_teacher_id and e.week_start = starts;
    else
        perform pg_advisory_xact_lock(hashtextextended('web-rph-weekly:' || p_teacher_id::text, 0));
        -- A retry at the week boundary can replay the previous completed export.
        -- It cannot spend the new week's allowance for the same request.
        select e.exports ->> p_export_id::text into existing_hash
        from public.web_rph_weekly_exports as e
        where e.teacher_id = p_teacher_id and e.week_start = starts - 7;
        if existing_hash is not null then
            select count(*)::integer into export_count
            from public.web_rph_weekly_exports as e
            cross join lateral jsonb_object_keys(e.exports)
            where e.teacher_id = p_teacher_id and e.week_start = starts;
            return query select existing_hash = p_content_hash, 2 - export_count, starts;
            return;
        end if;

        insert into public.web_rph_weekly_exports (teacher_id, week_start)
        values (p_teacher_id, starts) on conflict do nothing;
        select e.exports into saved
        from public.web_rph_weekly_exports as e
        where e.teacher_id = p_teacher_id and e.week_start = starts
        for update;
    end if;

    select count(*)::integer into export_count
    from jsonb_object_keys(coalesce(saved, '{}'::jsonb));
    if p_export_id is null then
        return query select export_count < 2, 2 - export_count, starts;
        return;
    end if;

    existing_hash := saved ->> p_export_id::text;
    if existing_hash is not null then
        return query select existing_hash = p_content_hash, 2 - export_count, starts;
    elsif export_count < 2 then
        update public.web_rph_weekly_exports as e
        set exports = saved || jsonb_build_object(p_export_id::text, p_content_hash)
        where e.teacher_id = p_teacher_id and e.week_start = starts;
        return query select true, 1 - export_count, starts;
    else
        return query select false, 0, starts;
    end if;
end;
$$;

revoke all on function public.web_rph_weekly_usage(bigint, uuid, text) from public, anon, authenticated;
grant execute on function public.web_rph_weekly_usage(bigint, uuid, text) to service_role;

commit;
