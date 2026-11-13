begin;

create table public.web_pbd_rosters (
    teacher_id bigint not null check (teacher_id > 0),
    class_name text not null check (char_length(class_name) between 1 and 40),
    school_year smallint not null check (school_year between 2020 and 2100),
    version uuid not null,
    students jsonb not null check (jsonb_typeof(students) = 'array' and jsonb_array_length(students) <= 100),
    primary key (teacher_id, class_name, school_year)
);

create table public.web_pbd_records (
    teacher_id bigint not null check (teacher_id > 0),
    class_name text not null check (char_length(class_name) between 1 and 40),
    school_year smallint not null check (school_year between 2020 and 2100),
    id uuid not null,
    version uuid not null,
    kind text not null check (kind in ('assessment', 'report')),
    record_date date not null,
    subject text not null check (char_length(subject) between 1 and 80),
    details jsonb not null check (jsonb_typeof(details) = 'object' and octet_length(details::text) <= 250000),
    primary key (teacher_id, class_name, school_year, id)
);

create index web_pbd_records_history
    on public.web_pbd_records (teacher_id, class_name, school_year, record_date desc, id desc);

alter table public.web_pbd_rosters enable row level security;
alter table public.web_pbd_records enable row level security;
revoke all on public.web_pbd_rosters, public.web_pbd_records from public, anon, authenticated, service_role;
grant select, insert, update on public.web_pbd_rosters to service_role;
grant select, insert, update, delete on public.web_pbd_records to service_role;

commit;
