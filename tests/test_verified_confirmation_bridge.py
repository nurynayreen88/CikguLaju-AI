import unittest
from datetime import date
from rph_hari_ini.session_eligibility import Eligibility, TimetableSession
from rph_hari_ini.verified_confirmation_bridge import check_verified_taught_action


class VerifiedConfirmationBridgeTests(unittest.TestCase):
    def setUp(self):
        session = TimetableSession(123, 2027, "class-uuid", "EN", "session-1",
                                   date(2027, 3, 1), 0, 160)
        self.eligibility = Eligibility(True, "eligible", session)
        self.kw = dict(eligibility=self.eligibility, teacher_id=123,
                       lesson_sequence=2, last_confirmed_sequence=1)

    def test_requires_explicit_action(self):
        self.assertEqual(check_verified_taught_action(**self.kw),
                         (False, "teacher_confirmation_required"))

    def test_valid_explicit_action(self):
        self.assertEqual(check_verified_taught_action(**self.kw, explicit_action=True),
                         (True, "eligible"))

    def test_unverified_session_rejected(self):
        kw = self.kw | {"eligibility": Eligibility(False, "blocked")}
        self.assertEqual(check_verified_taught_action(**kw, explicit_action=True),
                         (False, "unverified_session"))

    def test_wrong_teacher_rejected(self):
        kw = self.kw | {"teacher_id": 456}
        self.assertEqual(check_verified_taught_action(**kw, explicit_action=True),
                         (False, "teacher_mismatch"))

    def test_skipped_lesson_rejected(self):
        kw = self.kw | {"lesson_sequence": 7}
        self.assertEqual(check_verified_taught_action(**kw, explicit_action=True),
                         (False, "non_sequential"))


if __name__ == "__main__":
    unittest.main()
