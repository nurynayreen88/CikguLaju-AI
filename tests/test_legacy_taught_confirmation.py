import unittest
from datetime import date
from rph_hari_ini.session_eligibility import CalendarEvidence
from rph_hari_ini.legacy_taught_confirmation import confirm_from_legacy_timetable

CLASS_ID = "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb"


class LegacyTaughtTests(unittest.TestCase):
    def setUp(self):
        self.kw = dict(
            teacher_id=123, school_year=2027, session_date=date(2027, 3, 1),
            row={"day": "Isnin", "start": "08:00", "end": "09:00",
                 "class_name": "5 Amanah", "subject": "English"},
            lesson_total=160, registry={(123, 2027, "5 Amanah"): CLASS_ID},
            evidence=CalendarEvidence(2027, "Kedah", "TEST-ONLY",
                                      frozenset({date(2027, 3, 1)})),
            subject_key="EN", subject_mapping={"English": "EN"},
            lesson_sequence=2, last_confirmed_sequence=1)

    def test_explicit_confirmation(self):
        self.assertEqual(confirm_from_legacy_timetable(
            **self.kw, explicit_action=True), (True, "eligible"))

    def test_truthy_non_boolean_action_blocked(self):
        for action in (1, "true", ["confirm"]):
            with self.subTest(action=action):
                self.assertEqual(confirm_from_legacy_timetable(
                    **self.kw, explicit_action=action),
                    (False, "teacher_confirmation_required"))

    def test_other_teacher_cannot_confirm(self):
        kw = self.kw | {"teacher_id": 456}
        self.assertFalse(confirm_from_legacy_timetable(
            **kw, explicit_action=True)[0])

    def test_replay_same_lesson_blocked(self):
        kw = self.kw | {"lesson_sequence": 1}
        self.assertFalse(confirm_from_legacy_timetable(
            **kw, explicit_action=True)[0])

    def test_generation_does_not_confirm(self):
        self.assertEqual(confirm_from_legacy_timetable(**self.kw),
                         (False, "teacher_confirmation_required"))

    def test_skipping_lesson_blocked(self):
        kw = self.kw | {"lesson_sequence": 7}
        self.assertEqual(confirm_from_legacy_timetable(
            **kw, explicit_action=True), (False, "non_sequential"))

    def test_wrong_subject_mapping_blocked(self):
        kw = self.kw | {"subject_mapping": {"English": "BM"}}
        self.assertEqual(confirm_from_legacy_timetable(
            **kw, explicit_action=True), (False, "subject_mapping_mismatch"))

    def test_unverified_calendar_blocked(self):
        kw = self.kw | {"evidence": CalendarEvidence(2027, "Kedah", "TEST-ONLY", frozenset())}
        self.assertFalse(confirm_from_legacy_timetable(**kw, explicit_action=True)[0])


if __name__ == "__main__":
    unittest.main()
