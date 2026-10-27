import unittest
from datetime import date
from rph_hari_ini.session_eligibility import TimetableSession, CalendarEvidence
from rph_hari_ini.today_suggestion_bridge import suggest_today_lesson


class TodaySuggestionTests(unittest.TestCase):
    def setUp(self):
        self.session = TimetableSession(123, 2027, "class-id", "EN", "session-id",
                                        date(2027, 3, 1), 0, 160)
        self.evidence = CalendarEvidence(2027, "Kedah", "verified-test",
                                         frozenset({date(2027, 3, 1)}))
        self.kw = dict(session=self.session, evidence=self.evidence,
                       teacher_id=123, registered_class_keys=frozenset({"class-id"}),
                       expected_subject="EN", last_confirmed_sequence=1)

    def test_suggest_next_lesson(self):
        result = suggest_today_lesson(**self.kw)
        self.assertEqual((result.allowed, result.lesson_sequence), (True, 2))

    def test_no_calendar_date(self):
        kw = self.kw | {"evidence": CalendarEvidence(2027, "Kedah", "verified-test", frozenset())}
        self.assertEqual(suggest_today_lesson(**kw).reason, "unverified_session")

    def test_wrong_teacher(self):
        self.assertFalse(suggest_today_lesson(**(self.kw | {"teacher_id": 456})).allowed)

    def test_repeated_generation_no_progress(self):
        self.assertEqual(suggest_today_lesson(**self.kw), suggest_today_lesson(**self.kw))

    def test_all_lessons_complete(self):
        result = suggest_today_lesson(**(self.kw | {"last_confirmed_sequence": 160}))
        self.assertEqual(result.reason, "all_lessons_confirmed")


if __name__ == "__main__":
    unittest.main()
