begin;

set local lock_timeout = '3s';

alter table public.web_timetable_pdp_completion
    drop constraint web_timetable_pdp_completion_subject_code_check,
    add constraint web_timetable_pdp_completion_subject_code_check check (subject_code in (
        'ARAB', 'BM', 'ENGLISH', 'MATH', 'MORAL', 'MUZIK', 'PI', 'PJPK', 'PSV', 'RBT',
        'SCIENCE', 'SCIENCE_DLP', 'SEJARAH'
    )),
    add constraint web_timetable_pdp_completion_science_dlp_sequence_check check (
        subject_code <> 'SCIENCE_DLP'
        or sequence_no between 1 and 59
        or sequence_no between 101 and 110
    );

commit;
