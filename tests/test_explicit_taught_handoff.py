import unittest
from datetime import date
from rph_hari_ini.explicit_taught_handoff import check_taught_action
from rph_hari_ini.taught_confirmation_guard import Confirmation


class HandoffTests(unittest.TestCase):
    def test_generation_alone_cannot_confirm(self):
        self.assertEqual(check_taught_action(None),
                         (False, "teacher_confirmation_required"))

    def test_explicit_invalid_confirmation_rejected(self):
        self.assertEqual(check_taught_action(None, explicit_action=True),
                         (False, "invalid_confirmation"))

    def test_explicit_valid_confirmation(self):
        c = Confirmation("123", 2027, "5A", "EN", "session1",
                         date(2027, 3, 1), 2, 1, 160, True, True)
        self.assertEqual(check_taught_action(c, explicit_action=True),
                         (True, "eligible"))


if __name__ == "__main__":
    unittest.main()
