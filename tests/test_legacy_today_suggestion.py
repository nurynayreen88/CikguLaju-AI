import unittest
from datetime import date
from rph_hari_ini.session_eligibility import CalendarEvidence
from rph_hari_ini.legacy_today_suggestion import suggest_from_legacy_timetable

CLASS_ID = "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb"


class LegacyTodayTests(unittest.TestCase):
    def setUp(self):
        self.kw = dict(
            teacher_id=123, school_year=2027, session_date=date(2027, 3, 1),
            row={"day": "Isnin", "start": "08:00", "end": "09:00",
                 "class_name": "5 Amanah", "subject": "English"},
            lesson_total=160, registry={(123, 2027, "5 Amanah"): CLASS_ID},
            evidence=CalendarEvidence(2027, "Kedah", "TEST-ONLY",
                                      frozenset({date(2027, 3, 1)})),
            subject_key="EN", subject_mapping={"English": "EN"},
            last_confirmed_sequence=1)

    def test_next_lesson(self):
        result = suggest_from_legacy_timetable(**self.kw)
        self.assertEqual((result.allowed, result.lesson_sequence), (True, 2))

    def test_generation_does_not_advance(self):
        self.assertEqual(suggest_from_legacy_timetable(**self.kw),
                         suggest_from_legacy_timetable(**self.kw))

    def test_unverified_subject_blocked(self):
        result = suggest_from_legacy_timetable(**(self.kw | {"subject_mapping": None}))
        self.assertEqual(result.reason, "unverified_subject_mapping")

    def test_calendar_missing_blocked(self):
        evidence = CalendarEvidence(2027, "Kedah", "TEST-ONLY", frozenset())
        result = suggest_from_legacy_timetable(**(self.kw | {"evidence": evidence}))
        self.assertFalse(result.allowed)

    def test_finished_lessons(self):
        result = suggest_from_legacy_timetable(**(
            self.kw | {"last_confirmed_sequence": 160}))
        self.assertEqual(result.reason, "all_lessons_confirmed")


if __name__ == "__main__":
    unittest.main()
