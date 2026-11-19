begin;

set local lock_timeout = '3s';

alter table public.web_timetable_pdp_completion
    drop constraint web_timetable_pdp_completion_subject_code_check,
    add constraint web_timetable_pdp_completion_subject_code_check check (subject_code in (
        'ARAB', 'BM', 'ENGLISH', 'MATH', 'MATH_DLP', 'MORAL', 'MUZIK', 'PI', 'PJPK', 'PSV',
        'RBT', 'SCIENCE', 'SCIENCE_DLP', 'SEJARAH'
    )),
    add constraint web_timetable_pdp_completion_math_dlp_sequence_check check (
        subject_code <> 'MATH_DLP'
        or sequence_no between 1 and 69
        or sequence_no between 101 and 108
    );

commit;
