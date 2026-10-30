"""Validate the committed snapshot of the approved 2027 Google Sheet."""
import unittest
from pathlib import Path
from rpt_pj_2027_calendar import read_calendar_csv, school_days

ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data/rpt_pj_2027/calendar_2027_16_negeri_sheet_snapshot.csv"


class TestCalendarSnapshot(unittest.TestCase):
    def test_full_snapshot(self):
        records = read_calendar_csv(SNAPSHOT)
        self.assertEqual(len(records), 5840)
        self.assertEqual(len({state for state, _ in records}), 16)
        self.assertEqual(len(school_days(records, "Johor", "2027-01-04",
                                         "2027-01-10")), 5)

    def test_before_session_is_not_a_school_day(self):
        records = read_calendar_csv(SNAPSHOT)
        self.assertEqual(school_days(records, "Kedah", "2027-01-01",
                                     "2027-01-03"), [])


if __name__ == "__main__":
    unittest.main()
