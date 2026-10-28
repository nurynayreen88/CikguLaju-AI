import unittest
from datetime import date
from rph_hari_ini.stable_timetable_bridge import verified_stable_session
from rph_hari_ini.session_eligibility import CalendarEvidence

CLASS_ID = "f7bfb88c-ef6e-4d25-b08c-07d6b5a1d0bb"


class StableBridgeTests(unittest.TestCase):
    def setUp(self):
        self.row = {"day": "Isnin", "start": "08:00", "end": "09:00",
                    "class_name": "5 Amanah", "subject": "English"}
        self.evidence = CalendarEvidence(
            2027, "Kedah", "TEST-ONLY", frozenset({date(2027, 3, 1)}))
        self.kw = dict(
            teacher_id=123, school_year=2027, session_date=date(2027, 3, 1),
            row=self.row, lesson_total=160,
            registry={(123, 2027, "5 Amanah"): CLASS_ID},
            evidence=self.evidence, subject_key="EN",
            subject_mapping={"English": "EN"})

    def test_valid(self):
        allowed, reason, session = verified_stable_session(**self.kw)
        self.assertTrue(allowed, reason)
        self.assertEqual(session.class_key, CLASS_ID)

    def test_rename_stable_session_id(self):
        first = verified_stable_session(**self.kw)[2]
        renamed = dict(self.kw)
        renamed["row"] = self.row | {"class_name": "5 Cemerlang"}
        renamed["registry"] = {(123, 2027, "5 Cemerlang"): CLASS_ID}
        second = verified_stable_session(**renamed)[2]
        self.assertEqual(first.session_id, second.session_id)

    def test_whitespace_time_same_session_id(self):
        first = verified_stable_session(**self.kw)[2]
        padded = self.kw | {"row": self.row | {"start": " 08:00 ", "end": "09:00 "}}
        second = verified_stable_session(**padded)[2]
        self.assertEqual(first.session_id, second.session_id)

    def test_time_whitespace_keeps_session_identity(self):
        original = verified_stable_session(**self.kw)[2]
        changed = dict(self.kw)
        changed['row'] = self.row | {'start': ' 08:00 ', 'end': '09:00 '}
        result = verified_stable_session(**changed)[2]
        self.assertIsNotNone(result)
        self.assertEqual(original.session_id, result.session_id)

    def test_subject_mapping_missing_blocked(self):
        kw = self.kw | {"subject_mapping": None}
        allowed, reason, _ = verified_stable_session(**kw)
        self.assertFalse(allowed)
        self.assertEqual(reason, "unverified_subject_mapping")

    def test_subject_mapping_mismatch_blocked(self):
        kw = self.kw | {"subject_mapping": {"English": "BM"}}
        allowed, reason, _ = verified_stable_session(**kw)
        self.assertFalse(allowed)
        self.assertEqual(reason, "subject_mapping_mismatch")

    def test_unknown_class_blocked(self):
        kw = self.kw | {"registry": {}}
        allowed, _, session = verified_stable_session(**kw)
        self.assertFalse(allowed)
        self.assertIsNone(session)

    def test_calendar_missing_blocked(self):
        kw = self.kw | {"evidence": CalendarEvidence(2027, "Kedah", "", frozenset())}
        allowed, _, _ = verified_stable_session(**kw)
        self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
