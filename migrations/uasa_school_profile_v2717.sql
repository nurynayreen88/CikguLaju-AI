-- v27.17: Add optional school name to existing teacher profile.
-- Existing rows and other columns remain unchanged.
ALTER TABLE public.teacher_profiles ADD COLUMN IF NOT EXISTS school_name text;
