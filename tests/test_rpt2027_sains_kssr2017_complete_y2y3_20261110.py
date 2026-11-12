"""Source-code and PDF allocation gates for new Sains Year2/3 full annual RPT."""
import unittest
from collections import Counter
from pathlib import Path
import json

from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks
from rpt_2027.sains.sains_y2_y3_original_dskp_124_sp_20261110 import (
    source_records, SOURCE_SP_COUNTS, SOURCE_SHA256
)
from scripts.build_rpt2027_sains_kssr2017_complete_y2y3_20261110 import (
    annual_source_plan, PDP_TARGET
)

ROOT=Path(__file__).resolve().parents[1]
OFFICIAL_CODES=ROOT/"rpt_2027/sains/kssr2017_t2_t3_official_sp_code_ranges_20261107.json"


class SourceCompleteSainsY2Y3(unittest.TestCase):
    def test_match_original_124_official_dskp_codes_and_pages(self):
        index=json.loads(OFFICIAL_CODES.read_text("utf-8"))
        self.assertFalse(index["release_ready"])
        summary={int(x["year"]):x for x in index["pdfs"]}
        for year in (2,3):
            with self.subTest(year=year):
                official=summary[year]
                self.assertEqual(official["sha256"],SOURCE_SHA256[year])
                rows=source_records(year)
                self.assertEqual(len(rows),SOURCE_SP_COUNTS[year])
                self.assertEqual(len(rows),official["sp_count"])
                expected={f"{sk}.{n}" for sk,maxnum in official["sk_sp_max_suffix"].items()
                          for n in range(1,maxnum+1)}
                self.assertEqual({x["sp_code"] for x in rows}, expected)
                self.assertEqual([x["sp_code"] for x in rows],sorted(expected,key=lambda code:tuple(map(int,code.split(".")))))
                self.assertEqual(rows[0]["sp_code"],"1.1.1")
                self.assertTrue(all(x["sp_text"] and
                                    45<=x["original_pdf_page"]<=88 for x in rows))
        self.assertEqual(SOURCE_SP_COUNTS[2]+SOURCE_SP_COUNTS[3],124)

    def test_annual_92_and_103_pdp_full_source_no_invented_sp(self):
        cal=load_calendar_weeks()
        for year in (2,3):
            with self.subTest(year=year):
                rows=annual_source_plan(year)
                self.assertEqual(len(rows),PDP_TARGET[year])
                self.assertEqual([x["id"] for x in rows],
                                 [f"{n:03d}" for n in range(1,PDP_TARGET[year]+1)])
                self.assertEqual(rows[0]["week"],"M01")
                self.assertTrue(rows[0]["unit"].startswith("Unit 1"))
                self.assertEqual(sum(x["week"]=="M01" for x in rows),2)
                self.assertEqual(set(x["sp"] for x in rows),
                                 {x["sp_code"] for x in source_records(year)})
                self.assertEqual(sum(x["is_sourced_sp_practice"] for x in rows),
                                 PDP_TARGET[year]-SOURCE_SP_COUNTS[year])
                self.assertEqual(len({x["week"] for x in rows}),42)
                self.assertNotIn("M06",{x["week"] for x in rows})
                for row in rows:
                    self.assertFalse(row["academic_release_approved"])
                    self.assertNotIn("Padankan muka surat",row["note"])
                    self.assertIn("PBD: rekod evidens",row["note"])
                    self.assertFalse(row["official_sp_source_visual_signoff"])
                    self.assertFalse(row["rph_pdp_crosswalk_verified"])
                    self.assertEqual((row["a_start"],row["a_end"]),
                                     cal["A"][row["week"]])
                    self.assertEqual((row["b_start"],row["b_end"]),
                                     cal["B"][row["week"]])
                    self.assertIn(row["sp"]+" — ",row["sp_display"])

    def test_wrong_grade_rejected(self):
        for grade in (1,4,5,6,0,2027):
            with self.assertRaises(ValueError):
                annual_source_plan(grade)


if __name__=="__main__":
    unittest.main()
