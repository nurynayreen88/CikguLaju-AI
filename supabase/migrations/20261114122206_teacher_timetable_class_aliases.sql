ALTER TABLE public.teacher_profiles
    ADD COLUMN timetable_class_aliases jsonb NOT NULL DEFAULT '{}'::jsonb,
    ADD CONSTRAINT teacher_profiles_timetable_class_aliases_object
        CHECK (jsonb_typeof(timetable_class_aliases) = 'object');
