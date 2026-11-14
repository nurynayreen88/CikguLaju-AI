ALTER TABLE public.teacher_profiles
    ADD COLUMN timetable_subject_aliases jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT teacher_profiles_timetable_subject_aliases_object
        CHECK (jsonb_typeof(timetable_subject_aliases) = 'object');
