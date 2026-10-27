import unittest
from datetime import date
from rph_hari_ini.session_eligibility import (
    TimetableSession, CalendarEvidence, verify_session)


class EligibilityTests(unittest.TestCase):
    def setUp(self):
        self.session = TimetableSession(123, 2027, "5A", "EN", "s1",
                                        date(2027, 3, 1), 0, 160)
        self.evidence = CalendarEvidence(2027, "Kedah", "KPM-VERIFIED-TEST",
                                         frozenset({date(2027, 3, 1)}))
        self.kw = dict(teacher_id=123, registered_class_keys=frozenset({"5A"}),
                       expected_subject="EN")

    def test_valid(self):
        self.assertTrue(verify_session(self.session, self.evidence, **self.kw).allowed)

    def test_missing_evidence_object(self):
        self.assertEqual(verify_session(self.session, None, **self.kw).reason,
                         "invalid_evidence_or_session")

    def test_malformed_calendar_metadata(self):
        e = CalendarEvidence(2027, None, "TEST", self.evidence.verified_school_dates)
        self.assertEqual(verify_session(self.session, e, **self.kw).reason,
                         "unverified_calendar_source")

    def test_malformed_calendar_dates(self):
        e = CalendarEvidence(2027, "Kedah", "TEST", None)
        self.assertEqual(verify_session(self.session, e, **self.kw).reason,
                         "invalid_calendar_dates")

    def test_unverified_day(self):
        e = CalendarEvidence(2027, "Kedah", "KPM-VERIFIED-TEST", frozenset())
        self.assertEqual(verify_session(self.session, e, **self.kw).reason,
                         "not_verified_school_day")

    def test_missing_source(self):
        e = CalendarEvidence(2027, "Kedah", "", self.evidence.verified_school_dates)
        self.assertFalse(verify_session(self.session, e, **self.kw).allowed)

    def test_wrong_teacher(self):
        self.assertFalse(verify_session(self.session, self.evidence,
                         **(self.kw | {"teacher_id": 456})).allowed)

    def test_wrong_class(self):
        self.assertFalse(verify_session(self.session, self.evidence,
                         **(self.kw | {"registered_class_keys": frozenset()})).allowed)

    def test_wrong_subject(self):
        self.assertFalse(verify_session(self.session, self.evidence,
                         **(self.kw | {"expected_subject": "BM"})).allowed)

    def test_wrong_year(self):
        e = CalendarEvidence(2028, "Kedah", "TEST", self.evidence.verified_school_dates)
        self.assertFalse(verify_session(self.session, e, **self.kw).allowed)

    def test_wrong_weekday(self):
        s = TimetableSession(123, 2027, "5A", "EN", "s1",
                             date(2027, 3, 1), 1, 160)
        self.assertFalse(verify_session(s, self.evidence, **self.kw).allowed)


if __name__ == "__main__":
    unittest.main()
