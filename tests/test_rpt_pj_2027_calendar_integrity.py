"""Calendar completeness and state validation regression checks."""
import csv
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from rpt_pj_2027_calendar import (
    CalendarDataError, EXPECTED_STATES, GROUP_A, read_calendar_csv,
    validate_pdp_counts, school_days,
)


class CalendarIntegrityTests(unittest.TestCase):
    def make_csv(self, folder, *, skip=None):
        path = Path(folder) / "calendar.csv"
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=[
                "Tarikh", "Negeri", "Kumpulan", "Status PdP Dikira"])
            writer.writeheader()
            for state in sorted(EXPECTED_STATES):
                for offset in range(365):
                    day = date(2027, 1, 1) + timedelta(days=offset)
                    if (state, day.isoformat()) == skip:
                        continue
                    writer.writerow({
                        "Tarikh": day.isoformat(), "Negeri": state,
                        "Kumpulan": "A" if state in GROUP_A else "B",
                        "Status PdP Dikira": "CUTI",
                    })
        return path

    def test_complete_calendar(self):
        with tempfile.TemporaryDirectory() as folder:
            self.assertEqual(len(read_calendar_csv(self.make_csv(folder))), 5840)

    def test_missing_day_is_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_csv(folder, skip=("KEDAH", "2027-05-01"))
            with self.assertRaises(CalendarDataError):
                read_calendar_csv(path)

    def test_unknown_state_rejected_from_csv_in_non_strict_mode(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self.make_csv(folder)
            with path.open("a", newline="", encoding="utf-8") as stream:
                csv.writer(stream).writerow(["2027-01-01", "NEGERI REKAAN", "B", "CUTI"])
            with self.assertRaises(CalendarDataError):
                read_calendar_csv(path, strict=False)

    def test_unknown_state_rejected_by_school_day_query(self):
        with self.assertRaises(CalendarDataError):
            school_days({}, "NEGERI REKAAN", "2027-01-01", "2027-01-02")

    def test_zero_pdp_week_remains_empty(self):
        records = {("KEDAH", day.isoformat()): {"Status PdP Dikira": "CUTI"}
                   for day in (date(2027, 2, 7) + timedelta(days=i) for i in range(6))}
        self.assertEqual(school_days(records, "Kedah", "2027-02-07", "2027-02-12"), [])

    def test_missing_date_cannot_be_treated_as_school_day(self):
        with self.assertRaises(CalendarDataError):
            school_days({}, "Kedah", "2027-02-07", "2027-02-12")

    def test_unknown_state_rejected_by_pdp_catalogue(self):
        rows = [{"Negeri": "NEGERI REKAAN", "Tahun": 4, "PdP": i}
                for i in range(1, 35)]
        with self.assertRaises(CalendarDataError):
            validate_pdp_counts(rows)


if __name__ == "__main__":
    unittest.main()
