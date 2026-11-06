-- Applied to CikguLaju Supabase on 2026-11-06.
-- Additive avatar-only profile field; existing profile, timetable, quota,
-- payment, referral and entitlements are untouched.
ALTER TABLE public.teacher_profiles
ADD COLUMN IF NOT EXISTS avatar_code text NOT NULL DEFAULT 'initials'
CHECK (avatar_code IN ('initials','teacher','books','pencil','graduation',
                      'art','science','math','music','star','sun','flower'));
