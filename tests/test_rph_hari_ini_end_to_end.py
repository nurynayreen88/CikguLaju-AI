"""End-to-end pure-function test; progress changes only when caller persists it."""
import unittest
from datetime import date
from rph_hari_ini.session_eligibility import CalendarEvidence
from rph_hari_ini.legacy_today_suggestion import suggest_from_legacy_timetable
from rph_hari_ini.legacy_taught_confirmation import confirm_from_legacy_timetable

CLASS_ID = "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb"


class RphHariIniJourneyTests(unittest.TestCase):
    def setUp(self):
        self.kw = dict(
            teacher_id=123, school_year=2027, session_date=date(2027, 3, 1),
            row={"day": "Isnin", "start": "08:00", "end": "09:00",
                 "class_name": "5 Amanah", "subject": "English"},
            lesson_total=160, registry={(123, 2027, "5 Amanah"): CLASS_ID},
            evidence=CalendarEvidence(2027, "Kedah", "TEST-ONLY",
                                      frozenset({date(2027, 3, 1)})),
            subject_key="EN", subject_mapping={"English": "EN"})

    def suggestion(self, progress):
        return suggest_from_legacy_timetable(
            **self.kw, last_confirmed_sequence=progress)

    def confirmation(self, progress, explicit):
        return confirm_from_legacy_timetable(
            **self.kw, lesson_sequence=progress + 1,
            last_confirmed_sequence=progress, explicit_action=explicit)

    def test_generate_then_confirm_then_next_lesson(self):
        progress = 0  # authoritative taught progress, not generated count
        first = self.suggestion(progress)
        self.assertEqual(first.lesson_sequence, 1)
        # Generating and downloading RPH does not change taught progress.
        self.assertEqual(self.suggestion(progress).lesson_sequence, 1)
        self.assertEqual(self.confirmation(progress, False),
                         (False, "teacher_confirmation_required"))
        self.assertEqual(self.suggestion(progress).lesson_sequence, 1)
        self.assertEqual(self.confirmation(progress, True), (True, "eligible"))
        # Only a separate trusted, atomic DB write could advance progress.
        self.assertEqual(self.suggestion(progress).lesson_sequence, 1)
        progress = 1  # simulate successful externally persisted confirmation
        self.assertEqual(self.suggestion(progress).lesson_sequence, 2)

    def test_unverified_calendar_blocks_both_actions(self):
        self.kw["evidence"] = CalendarEvidence(2027, "Kedah", "TEST-ONLY", frozenset())
        self.assertFalse(self.suggestion(0).allowed)
        self.assertFalse(self.confirmation(0, True)[0])


if __name__ == "__main__":
    unittest.main()
