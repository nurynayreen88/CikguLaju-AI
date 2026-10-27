import unittest
from datetime import date
from rph_hari_ini.taught_confirmation_guard import Confirmation, validate_confirmation


class GuardTests(unittest.TestCase):
    def make(self, **changes):
        d = dict(teacher_id="123", school_year=2027, class_id="5A",
                 subject_id="English", session_instance_id="2027-03-01/5A/EN/0800",
                 session_date=date(2027, 3, 1), lesson_sequence=2,
                 last_confirmed_sequence=1, lesson_total=160,
                 calendar_verified=True, session_verified=True)
        d.update(changes)
        return Confirmation(**d)

    def test_invalid_object(self):
        self.assertEqual(validate_confirmation(None).reason, "invalid_confirmation")

    def test_truthy_string_flags_rejected(self):
        self.assertEqual(validate_confirmation(self.make(calendar_verified="yes")).reason,
                         "unverified_calendar_or_session")

    def test_datetime_rejected(self):
        from datetime import datetime
        self.assertEqual(validate_confirmation(self.make(
            session_date=datetime(2027, 3, 1, 8, 0))).reason, "invalid_session_date")

    def test_boolean_school_year_rejected(self):
        self.assertEqual(validate_confirmation(self.make(school_year=True)).reason,
                         "invalid_school_year")

    def test_valid(self):
        self.assertTrue(validate_confirmation(self.make()).allowed)

    def test_unverified_calendar(self):
        self.assertEqual(validate_confirmation(self.make(calendar_verified=False)).reason,
                         "unverified_calendar_or_session")

    def test_unverified_session(self):
        self.assertFalse(validate_confirmation(self.make(session_verified=False)).allowed)

    def test_year_rollover(self):
        self.assertEqual(validate_confirmation(self.make(school_year=2028)).reason,
                         "invalid_session_date")

    def test_generation_does_not_confirm_progress(self):
        generated_rph_count = 7
        last_confirmed_sequence = 1
        decision = validate_confirmation(self.make(
            lesson_sequence=generated_rph_count,
            last_confirmed_sequence=last_confirmed_sequence))
        self.assertFalse(decision.allowed)
        self.assertEqual(decision.reason, "non_sequential")

    def test_skip(self):
        self.assertEqual(validate_confirmation(self.make(lesson_sequence=3)).reason,
                         "non_sequential")

    def test_replay(self):
        self.assertFalse(validate_confirmation(self.make(lesson_sequence=1)).allowed)

    def test_end_of_sequence(self):
        self.assertFalse(validate_confirmation(self.make(lesson_sequence=161,
                         last_confirmed_sequence=160)).allowed)

    def test_nonstring_identity_rejected(self):
        for field in ("teacher_id", "class_id", "subject_id", "session_instance_id"):
            with self.subTest(field=field):
                self.assertEqual(validate_confirmation(self.make(**{field: None})).reason,
                                 "missing_identity")

    def test_missing_identity(self):
        self.assertEqual(validate_confirmation(self.make(class_id="")).reason,
                         "missing_identity")

    def test_boolean_sequence(self):
        self.assertEqual(validate_confirmation(self.make(lesson_sequence=True)).reason,
                         "invalid_sequence_type")


if __name__ == "__main__":
    unittest.main()
