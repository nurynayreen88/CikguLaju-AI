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
        self.assertEqual(audit["overall_counts"].get(
            "sejarah_week_derived_from_candidate_dates"), 105)
        self.assertEqual(audit["overall_counts"].get(
            "sejarah_group_a_kpm_holiday_indexed"), 3)
        self.assertEqual(audit["overall_counts"].get("no_week_with_candidate_dates", 0), 0)
        self.assertEqual(len(audit["by_pdf"]), 21)
        self.assertEqual(audit["status"], "AUDIT_ONLY_NOT_FINAL_RELEASE")
        self.assertIn(audit["release_gate"], (
            "BLOCKED", "CALENDAR_WEEK_ALIGNED_ONLY_NOT_CURRICULUM_APPROVAL"
        ))
        self.assertTrue(all(sum(item["status_counts"].values()) == item["total_pdp"]
                            for item in audit["by_pdf"]))

    def test_same_calendar_dates_with_wrong_label_is_a_relabel_candidate(self):
        master = read_master()
        row = {"id": "001", "week": "M06",
               "a_start": master["A"]["M07"]["start"],
               "a_end": master["A"]["M07"]["end"],
               "b_start": master["B"]["M07"]["start"],
               "b_end": master["B"]["M07"]["end"]}
        prior = dict(row)
        result = audit_rows("psv", 2, [row], master)
        self.assertEqual(result["status_counts"],
                         {"source_week_label_conflicts_with_master": 1})
        self.assertEqual(result["examples"][0]["suggested_master_week_label_only"], "M07")
        self.assertEqual(row, prior, "Read-only calendar audit must never change source rows")

    def test_psv_source_week_preserved_and_display_matches_master(self):
        from scripts.build_rpt_2027_standard_preview import psv_records
        from rpt_2027.common.calendar_week_mapping_staging import (
            matching_master_weeks, load_calendar_weeks
        )
        master = load_calendar_weeks()
        for year in range(2, 7):
            rows = psv_records(year)
            self.assertEqual(len(rows), 42)
            self.assertEqual(sum(bool(x.get("source_week")) for x in rows), 37)
            self.assertEqual(rows[5]["source_week"], "M06")
            self.assertEqual(rows[5]["week"], "M07")
            self.assertEqual(rows[5]["a_start"], "2027-02-14")
            self.assertEqual(rows[5]["b_start"], "2027-02-15")
            for row in rows:
                self.assertEqual(matching_master_weeks(row, master), [row["week"]])
        report = audit_all()
        self.assertEqual(report["overall_counts"].get("week_label_reconciled_from_master"), 185)
        self.assertEqual(report["overall_counts"].get("week_and_date_mismatch", 0), 0)

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
