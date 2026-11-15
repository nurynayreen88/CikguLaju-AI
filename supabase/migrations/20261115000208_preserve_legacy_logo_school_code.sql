ALTER TABLE public.teacher_profiles
  ADD COLUMN IF NOT EXISTS legacy_logo_school_code text;

-- Keep account-level logos readable for the school originally saved at rollout.
-- New uploads use school-specific paths. The old object remains in place.
UPDATE public.teacher_profiles
SET legacy_logo_school_code = school_code
WHERE legacy_logo_school_code IS NULL
  AND school_code IS NOT NULL
  AND school_code <> '';

NOTIFY pgrst, 'reload schema';
