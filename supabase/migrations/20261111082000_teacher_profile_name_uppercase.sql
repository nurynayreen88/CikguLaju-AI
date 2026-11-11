-- Normalize Nama Guru for BOTH Web and Telegram.
-- Existing profiles: only display_name changes. Do not touch updated_at,
-- classes, timetable JSON, quotas, payment records, or school links.
CREATE OR REPLACE FUNCTION public.teacher_profile_uppercase_display_name()
RETURNS trigger
LANGUAGE plpgsql
SET search_path = pg_catalog
AS $$
BEGIN
  IF NEW.display_name IS NOT NULL THEN
    NEW.display_name := upper(NEW.display_name);
  END IF;
  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS teacher_profile_uppercase_display_name_on_write
  ON public.teacher_profiles;

CREATE TRIGGER teacher_profile_uppercase_display_name_on_write
BEFORE INSERT OR UPDATE OF display_name
ON public.teacher_profiles
FOR EACH ROW
EXECUTE FUNCTION public.teacher_profile_uppercase_display_name();

UPDATE public.teacher_profiles
SET display_name = upper(display_name)
WHERE display_name IS NOT NULL
  AND display_name IS DISTINCT FROM upper(display_name);
