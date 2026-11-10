"""Verify new source-grounded annual Sains RPT content before any release."""
from collections import Counter
import unittest

from scripts.build_rpt2027_sains_kssr2017_complete_y4y5_20261110 import (
    _source, annual_source_plan, SOURCE_COUNTS, PDP_TARGETS,
)
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks


class OfficialSainsRPTSourcePlan(unittest.TestCase):
    def test_all_186_official_sp_codes_covered_in_y4_y5(self):
        calendar = load_calendar_weeks()
        total_codes=0
        total_lessons=0
        for year in (4,5):
            with self.subTest(year=year):
                src=_source(year)
                source_codes={r["sp_code"] for r in src}
                self.assertEqual(len(source_codes),SOURCE_COUNTS[year])
                rows=annual_source_plan(year)
                self.assertEqual(len(rows),PDP_TARGETS[year])
                self.assertEqual(rows[0]["week"],"M01")
                self.assertTrue(rows[0]["unit"].startswith("Unit 1:"))
                self.assertEqual([x["id"] for x in rows],
                                 [f"{n:03d}" for n in range(1,len(rows)+1)])
                used=[code for row in rows for code in row["source_official_sp_codes"]]
                counts=Counter(used)
                self.assertEqual(set(counts),source_codes)
                self.assertEqual(sum(c-1 for c in counts.values()),
                                 0 if year==4 else 21)
                for row in rows:
                    week=row["week"]
                    self.assertEqual((row["a_start"],row["a_end"]), calendar["A"][week])
                    self.assertEqual((row["b_start"],row["b_end"]), calendar["B"][week])
                    self.assertFalse(row["academic_release_approved"])
                    self.assertIn("PBD: kumpulkan evidens", row["note"])
                    self.assertNotIn("semak hasil kerja", row["note"])
                    self.assertNotEqual(row["topic"], row["sk_display"].split(" — ",1)[-1])
                    self.assertTrue(row["topic"])
                    self.assertFalse(row["teacher_approved"])
                    self.assertFalse(row["rph_2027_crosswalk_verified"])
                    self.assertFalse(row["original_sp_text_visual_signoff"])
                    for code in row["source_official_sp_codes"]:
                        self.assertIn(code+" — ",row["sp_display"])
                total_codes+=len(source_codes)
                total_lessons+=len(rows)
        self.assertEqual(total_codes,186)
        self.assertEqual(total_lessons,204)

    def test_source_original_records_not_edited(self):
        before=_source(4),_source(5)
        annual_source_plan(4)
        annual_source_plan(5)
        self.assertEqual(before,(_source(4),_source(5)))

    def test_invalid_cohort_blocked(self):
        for year in (1,2,3,6):
            with self.assertRaises(ValueError):
                annual_source_plan(year)


if __name__=="__main__":
    unittest.main()
