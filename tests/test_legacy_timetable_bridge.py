import unittest
from datetime import date
from rph_hari_ini.legacy_timetable_bridge import candidate_from_legacy_row, check_legacy_row
from rph_hari_ini.session_eligibility import CalendarEvidence


class LegacyBridgeTests(unittest.TestCase):
    def setUp(self):
        self.row = {"day": "Isnin", "start": "08:00", "end": "09:00",
                    "class_name": "5 Amanah", "subject": "English"}
        self.date = date(2027, 3, 1)
        self.kw = dict(teacher_id=123, school_year=2027,
                       session_date=self.date, row=self.row, lesson_total=160)

    def test_valid_candidate(self):
        self.assertIsNotNone(candidate_from_legacy_row(**self.kw))

    def test_wrong_day(self):
        self.assertIsNone(candidate_from_legacy_row(**(self.kw | {
            "row": self.row | {"day": "Selasa"}})))

    def test_bad_time(self):
        self.assertIsNone(candidate_from_legacy_row(**(self.kw | {
            "row": self.row | {"start": "8am"}})))

    def test_reverse_time(self):
        self.assertIsNone(candidate_from_legacy_row(**(self.kw | {
            "row": self.row | {"end": "07:00"}})))

    def test_unverified_calendar(self):
        evidence = CalendarEvidence(2027, "Kedah", "", frozenset({self.date}))
        allowed, reason, _ = check_legacy_row(
            **self.kw, evidence=evidence, registered_class_keys=frozenset({"5 Amanah"}))
        self.assertFalse(allowed)
        self.assertEqual(reason, "unverified_calendar_source")

    def test_verified_test_calendar(self):
        evidence = CalendarEvidence(2027, "Kedah", "TEST-ONLY", frozenset({self.date}))
        allowed, _, _ = check_legacy_row(
            **self.kw, evidence=evidence, registered_class_keys=frozenset({"5 Amanah"}))
        self.assertTrue(allowed)


if __name__ == "__main__":
    unittest.main()
