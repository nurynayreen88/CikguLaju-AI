import csv
import tempfile
import unittest
from pathlib import Path

from rpt_pj_2027_calendar import (
    CalendarDataError, can_download_rpt, read_calendar_csv,
    school_days, validate_pdp_counts,
)


class TestRPTPJ2027(unittest.TestCase):
    def test_access_gate(self):
        self.assertFalse(can_download_rpt())
        self.assertFalse(can_download_rpt(subscription_active=False))
        self.assertTrue(can_download_rpt(subscription_active=True))
        self.assertTrue(can_download_rpt(rakan_pembangun_active=True))
        self.assertTrue(can_download_rpt(is_developer=True))

    def test_calendar(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "calendar.csv"
            with path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=[
                    "Tarikh", "Negeri", "Kumpulan", "Status PdP Dikira"])
                writer.writeheader()
                writer.writerow({"Tarikh": "2027-01-04", "Negeri": "Johor",
                                 "Kumpulan": "B", "Status PdP Dikira": "CALON PDP"})
                writer.writerow({"Tarikh": "2027-01-05", "Negeri": "Johor",
                                 "Kumpulan": "B", "Status PdP Dikira": "CUTI NEGERI"})
            records = read_calendar_csv(path, strict=False)
            self.assertEqual(school_days(records, "Johor", "2027-01-04",
                                         "2027-01-05"), ["2027-01-04"])
            with self.assertRaises(CalendarDataError):
                read_calendar_csv(path, strict=True)

    def test_sequence(self):
        rows = [{"Negeri": "Johor", "Tahun": 5, "PdP": i}
                for i in range(1, 34)]
        self.assertEqual(validate_pdp_counts(rows), 1)
        with self.assertRaises(CalendarDataError):
            validate_pdp_counts(rows[:-1])


if __name__ == "__main__":
    unittest.main()
