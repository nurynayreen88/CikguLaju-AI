begin;

create table public.web_timetable_pdp_completion (
    teacher_id bigint not null check (teacher_id > 0),
    class_key text not null check (char_length(class_key) between 1 and 80),
    subject_code text not null check (subject_code in (
        'ARAB', 'BM', 'ENGLISH', 'MATH', 'MORAL', 'MUZIK', 'PI', 'PJPK', 'PSV', 'RBT', 'SCIENCE', 'SEJARAH'
    )),
    component text not null check (
        (subject_code = 'PJPK' and component in ('PJ', 'PK')) or
        (subject_code <> 'PJPK' and component = '')
    ),
    pdp_date date not null,
    start_time time not null,
    sequence_no smallint not null check (sequence_no between 1 and 999),
    primary key (teacher_id, class_key, subject_code, pdp_date, start_time)
);

create index web_timetable_pdp_teacher_date
    on public.web_timetable_pdp_completion (teacher_id, pdp_date);

alter table public.web_timetable_pdp_completion enable row level security;
revoke all on public.web_timetable_pdp_completion from public, anon, authenticated, service_role;
grant select, insert, update, delete on public.web_timetable_pdp_completion to service_role;

create function public.web_timetable_pdp_progress(p_teacher_id bigint, p_target date)
returns table (class_key text, subject_code text, component text, pdp_date date,
               start_time time, sequence_no smallint)
language sql stable security invoker set search_path = ''
as $$
    select c.class_key, c.subject_code, c.component, c.pdp_date, c.start_time, c.sequence_no
    from public.web_timetable_pdp_completion as c
    where c.teacher_id = p_teacher_id and c.pdp_date = p_target
    union all
    select previous.* from (
        select distinct on (c.class_key, c.subject_code, c.component)
            c.class_key, c.subject_code, c.component, c.pdp_date, c.start_time, c.sequence_no
        from public.web_timetable_pdp_completion as c
        where c.teacher_id = p_teacher_id and c.pdp_date < p_target
          and c.pdp_date >= date_trunc('year', p_target::timestamp)::date
        order by c.class_key, c.subject_code, c.component, c.pdp_date desc, c.start_time desc
    ) as previous;
$$;

revoke all on function public.web_timetable_pdp_progress(bigint, date) from public, anon, authenticated;
grant execute on function public.web_timetable_pdp_progress(bigint, date) to service_role;

commit;
