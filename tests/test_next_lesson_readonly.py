import unittest
from datetime import date
from rph_hari_ini.session_eligibility import Eligibility, TimetableSession
from rph_hari_ini.next_lesson_readonly import suggest_next_lesson


class NextLessonTests(unittest.TestCase):
    def setUp(self):
        session = TimetableSession(123, 2027, "class-uuid", "EN", "session-1",
                                   date(2027, 3, 1), 0, 160)
        self.eligibility = Eligibility(True, "eligible", session)

    def test_next_lesson(self):
        result = suggest_next_lesson(eligibility=self.eligibility,
                                     last_confirmed_sequence=1)
        self.assertEqual((result.allowed, result.lesson_sequence), (True, 2))

    def test_repeated_generation_does_not_advance(self):
        first = suggest_next_lesson(eligibility=self.eligibility,
                                    last_confirmed_sequence=1)
        second = suggest_next_lesson(eligibility=self.eligibility,
                                     last_confirmed_sequence=1)
        self.assertEqual(first, second)

    def test_completed_sequence(self):
        result = suggest_next_lesson(eligibility=self.eligibility,
                                     last_confirmed_sequence=160)
        self.assertEqual(result.reason, "all_lessons_confirmed")

    def test_invalid_progress(self):
        for value in (-1, 161, True, None):
            with self.subTest(value=value):
                self.assertEqual(suggest_next_lesson(
                    eligibility=self.eligibility,
                    last_confirmed_sequence=value).reason, "invalid_progress")

    def test_unverified_session(self):
        result = suggest_next_lesson(eligibility=Eligibility(False, "blocked"),
                                     last_confirmed_sequence=1)
        self.assertEqual(result.reason, "unverified_session")


if __name__ == "__main__":
    unittest.main()
