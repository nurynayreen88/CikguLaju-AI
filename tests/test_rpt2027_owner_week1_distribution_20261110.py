"""Week-01 Years2-6 RPT owner plan: sourced sequence and academic safeguards."""
from __future__ import annotations

from collections import Counter
from copy import deepcopy
import unittest

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.common.week1_owner_plan_20261110 import (
    CANDIDATE_WEEKS, PLAN_STATUS, move_first_sessions_to_m01,
    allocate_arabic_weeks, allocate_rbt_weeks,
)
from scripts.build_rpt_2027_remaining_four_subjects_staging import (
    bm_records, pi_records, arabic_records, week1_proposed_records,
)
from scripts.build_rpt_2027_standard_preview import rbt_records
from scripts.build_rpt_2027_sains_342_actual_source_staging import source_records

FIELDS = ("id", "unit", "topic", "sk", "sp", "sk_display", "sp_display")


def original_identity(rows):
    return [{key: row.get(key) for key in FIELDS} for row in rows]


class OwnerRPTWeek01QA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cal = load_calendar_weeks()

    def assert_cal_dates(self, rows):
        for r in rows:
            week = r.get("week")
            self.assertIn(week, self.cal["A"])
            self.assertEqual((r["a_start"], r["a_end"]), self.cal["A"][week])
            self.assertEqual((r["b_start"], r["b_end"]), self.cal["B"][week])

    def test_bm_5_years_begin_3_pdp_in_m01(self):
        counts = {2: 164, 3: 165, 4: 165, 5: 166, 6: 165}
        for year, n in counts.items():
            with self.subTest(year=year):
                src = bm_records(year)
                before = deepcopy(src)
                rows = week1_proposed_records("bahasa_melayu", year, bm_records)
                self.assertEqual(src, before, "original source records must not mutate")
                self.assertEqual(len(rows), n)
                self.assertEqual(original_identity(src), original_identity(rows))
                self.assertEqual([r["week"] for r in rows[:3]], ["M01"] * 3)
                self.assertEqual(rows[3]["week"], "M02")
                self.assertEqual([r["week"] for r in src[:5]], ["M02"] * 5)
                self.assertEqual(Counter(r["week"] for r in rows)["M01"], 3)
                self.assertEqual(Counter(r["week"] for r in rows)["M02"], 2)
                self.assertTrue(all(r.get("week_allocation") == PLAN_STATUS
                                    and r.get("academic_week_signoff") is False
                                    for r in rows[:3]))
                self.assert_cal_dates(rows)

    def test_bm_week01_three_pdp_share_one_merged_week_cell(self):
        from rpt_2027.common.format_2026_layout_preview import week_merge_ranges
        for year in range(2, 7):
            with self.subTest(year=year):
                rows = week1_proposed_records("bahasa_melayu", year, bm_records)
                groups = week_merge_ranges(
                    rows, max_rows_per_group=2, first_group_max_rows=3)
                self.assertEqual(groups[0], (1, 3))
                self.assertTrue(all(last-first+1 <= 2 for first,last in groups[1:]))
                self.assertEqual([r["id"] for r in rows[:3]], ["001", "002", "003"])
                self.assertEqual([r["week"] for r in rows[:3]], ["M01"] * 3)
                self.assertEqual(rows[3]["week"], "M02")

    def test_pi_5_years_begin_2_pdp_in_m01_and_preserve_holds(self):
        counts = {2: 112, 3: 147, 4: 151, 5: 143, 6: 143}
        for year, n in counts.items():
            with self.subTest(year=year):
                src = pi_records(year)
                before = deepcopy(src)
                rows = week1_proposed_records("pendidikan_islam", year, pi_records)
                self.assertEqual(src, before)
                self.assertEqual(len(rows), n)
                self.assertEqual(original_identity(src), original_identity(rows))
                self.assertEqual([r["week"] for r in rows[:2]], ["M01", "M01"])
                self.assertEqual(rows[2]["week"], "M02")
                self.assertEqual(src[0]["week"], "M02")
                self.assertEqual(Counter(r["week"] for r in rows)["M01"], 2)
                self.assertEqual(sum(bool(r.get("source_held")) for r in rows),
                                 sum(bool(r.get("source_held")) for r in src))
                self.assertTrue(all(r.get("academic_week_signoff") is False
                                    for r in rows[:2]))
                self.assert_cal_dates(rows)

    def test_arabic_5_years_have_m01_and_no_blank_weeks(self):
        counts = {2: 60, 3: 60, 4: 58, 5: 60, 6: 60}
        for year, n in counts.items():
            with self.subTest(year=year):
                src = arabic_records(year)
                before = deepcopy(src)
                rows = week1_proposed_records("bahasa_arab", year, arabic_records)
                self.assertEqual(src, before)
                self.assertEqual(len(rows), n)
                self.assertEqual(original_identity(src), original_identity(rows))
                tally = Counter(r["week"] for r in rows)
                self.assertEqual(tally["M01"], 1)
                self.assertEqual(set(tally), set(CANDIDATE_WEEKS))
                self.assertTrue(all(1 <= value <= 2 for value in tally.values()))
                self.assertEqual(sum(tally.values()), n)
                self.assertTrue(all(r.get("academic_week_signoff") is False
                                    and r["week_allocation"] == PLAN_STATUS
                                    for r in rows))
                self.assert_cal_dates(rows)

    def test_rbt_3_years_one_pdp_m01_and_spaced_32_weeks(self):
        for year in (4, 5, 6):
            with self.subTest(year=year):
                src = rbt_records(year)
                before = deepcopy(src)
                rows = allocate_rbt_weeks(src, year=year)
                self.assertEqual(src, before)
                self.assertEqual(original_identity(src), original_identity(rows))
                self.assertEqual(len(rows), 32)
                tally = Counter(r["week"] for r in rows)
                self.assertEqual(tally["M01"], 1)
                self.assertEqual(len(tally), 32)
                self.assertEqual(max(tally.values()), 1)
                self.assertEqual(rows[-1]["week"], "M43")
                self.assertNotIn("M06", tally)
                self.assertTrue(all(r.get("academic_week_signoff") is False
                                    and r.get("class_date_confirmed") is False
                                    for r in rows))
                self.assert_cal_dates(rows)

    def test_sains_5_years_staging_already_m01(self):
        years = source_records()
        self.assertEqual(set(years), {2, 3, 4, 5, 6})
        self.assertEqual(sum(len(rows) for rows in years.values()), 342)
        for year, rows in years.items():
            with self.subTest(year=year):
                self.assertEqual(rows[0]["week"], "M01")
                self.assertEqual(rows[0]["id"], "001")
                self.assertIn("M02", {r["week"] for r in rows})
                self.assert_cal_dates(rows)

    def test_refuse_year1_and_existing_week_allocations(self):
        sample = bm_records(2)
        with self.assertRaises(ValueError):
            move_first_sessions_to_m01(
                sample, subject="bahasa_melayu", year=1, sessions=3)
        with self.assertRaises(ValueError):
            move_first_sessions_to_m01(
                sample, subject="bahasa_melayu", year=2, sessions=5)
        with self.assertRaises(ValueError):
            move_first_sessions_to_m01(
                sample, subject="bahasa_melayu", year=2, sessions=0)
        with self.assertRaises(ValueError):
            allocate_arabic_weeks(arabic_records(2), year=1)
        with self.assertRaises(ValueError):
            allocate_rbt_weeks(rbt_records(4), year=1)
        allocated = allocate_rbt_weeks(rbt_records(4), year=4)
        with self.assertRaises(ValueError):
            allocate_rbt_weeks(allocated, year=4)


if __name__ == "__main__":
    unittest.main()
