"""Read-only reconciliation of all staged RPTs with central 2027 A/B week master."""
import unittest

from scripts.audit_rpt_2027_calendar_master_staging import (
    read_master, audit_rows, audit_all
)


class CalendarWeekAuditQA(unittest.TestCase):
    def test_master_has_44_sourced_weeks_per_group(self):
        master = read_master()
        self.assertEqual(set(master), {"A", "B"})
        for group in ("A", "B"):
            self.assertEqual(len(master[group]), 44)
            self.assertEqual(master[group]["M01"]["start"], "2027-01-04")
            self.assertEqual(master[group]["M44"]["end"],
                             "2027-12-02" if group == "A" else "2027-12-03")

    def test_21_pdf_coverage_and_no_silent_date_assignments(self):
        audit = audit_all()
        self.assertEqual(audit["total_pdfs"], 21)
        self.assertEqual(audit["total_pdp"], 1233)
        self.assertEqual(sum(audit["overall_counts"].values()), 1233)
        self.assertEqual(len(audit["by_pdf"]), 21)
        self.assertEqual(audit["status"], "AUDIT_ONLY_NOT_FINAL_RELEASE")
        self.assertIn(audit["release_gate"], (
            "BLOCKED", "CALENDAR_WEEK_ALIGNED_ONLY_NOT_CURRICULUM_APPROVAL"
        ))
        self.assertTrue(all(sum(item["status_counts"].values()) == item["total_pdp"]
                            for item in audit["by_pdf"]))

    def test_missing_week_not_invented(self):
        master = read_master()
        sample = {"id": "001", "week": "Agihan cadangan",
                  "a_start": "2027-01-04", "a_end": "2027-01-07",
                  "b_start": "2027-01-04", "b_end": "2027-01-08"}
        result = audit_rows("sejarah", 4, [sample], master)
        self.assertEqual(result["status_counts"], {"no_week_with_candidate_dates": 1})
        self.assertTrue(result["requires_review"])
        sample["week"] = "M01"
        result = audit_rows("sejarah", 4, [sample], master)
        self.assertEqual(result["status_counts"], {"aligned_to_master_week": 1})


if __name__ == "__main__":
    unittest.main()
