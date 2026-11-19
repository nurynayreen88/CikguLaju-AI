begin;

set local lock_timeout = '3s';

-- Year 5 Science adds Lesson 60. The Web verifies each class's year-specific range.
alter table public.web_timetable_pdp_completion
    drop constraint web_timetable_pdp_completion_science_dlp_sequence_check,
    add constraint web_timetable_pdp_completion_science_dlp_sequence_check check (
        subject_code <> 'SCIENCE_DLP'
        or sequence_no between 1 and 60
        or sequence_no between 101 and 110
    );

commit;
