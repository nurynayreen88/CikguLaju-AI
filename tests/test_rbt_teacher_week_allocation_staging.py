"""RBT actual 2027 week candidates require all 32 explicit teacher decisions."""
import json
import tempfile
from pathlib import Path
import unittest
from rpt_2027.common.rbt_teacher_week_allocation_staging import (
  assign_rbt_weeks_from_teacher_manifest as propose, VALID_STATUS,
  build_teacher_rbt_preview
)
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

def teacher_manifest(y,labels=None):
    labels=labels if labels is not None else [f"M{i:02d}" for i in range(3,35)]
    return {
      "academic_year":2027, "year":y, "status":VALID_STATUS,
      "school_calendar_verified":False,
      "source_reference":"Provisional actual school timetable supplied by teacher",
      "pdp_to_week":[{"pdp":i,"week":week} for i,week in enumerate(labels,1)]
    }

class TeacherExplicitRBT2027WeeksQA(unittest.TestCase):
    def test_all_32_explicit_week_candidates_and_staged_calendar_dates(self):
        cal=load_calendar_weeks()
        for year in (4,5,6):
            rows=propose(year,teacher_manifest(year))
            self.assertEqual(len(rows),32)
            for i,row in enumerate(rows,1):
                label=f"M{i+2:02d}"
                self.assertEqual(row["source_proposed_week"],label)
                self.assertEqual(row["week"],label+" (CADANGAN GURU)")
                self.assertEqual((row["a_start"],row["a_end"]),cal["A"][label])
                self.assertEqual((row["b_start"],row["b_end"]),cal["B"][label])
                self.assertEqual(row["schedule_status"],VALID_STATUS)
                self.assertIs(row["school_calendar_verified"],False)
                self.assertIn("bukan tarikh PdP sebenar",row["note"])

    def test_explicit_teacher_manifest_can_render_separate_review_only_pdf(self):
        with tempfile.TemporaryDirectory() as td:
            t=Path(td)
            manifest=t/"teacher_input.json"
            manifest.write_text(json.dumps(teacher_manifest(4)),encoding="utf-8")
            dest=t/"RBT_TAHUN4_SCHOOL_STAGING_REVIEW.pdf"
            result=build_teacher_rbt_preview(4,manifest,dest)
            self.assertEqual(result,dest)
            self.assertTrue(result.is_file())
            self.assertGreater(result.stat().st_size,5000)
            with self.assertRaises(ValueError):
                build_teacher_rbt_preview(4,manifest,t/"official.pdf")

    def test_unsourced_or_invalid_calendar_never_becomes_an_rpt(self):
        y=4
        baseline=teacher_manifest(y)
        cases=[
          {"pdp_to_week":[]},
          {"source_reference":""},
          {"school_calendar_verified":True},
          {"academic_year":2026},
          {"year":3},
          {"status":"FINAL_READY"},
          {"pdp_to_week":[{"pdp":1,"week":"M03"}]},
          {"pdp_to_week":[{"pdp":i,"week":"M45"} for i in range(1,33)]},
          {"pdp_to_week":[{"pdp":i,"week":"M00"} for i in range(1,33)]},
          {"pdp_to_week":[{"pdp":i,"week":"M02"} if i==17 else {"pdp":i,"week":f"M{i+2:02d}"} for i in range(1,33)]},
          {"pdp_to_week":[{"pdp":i+1,"week":f"M{i+2:02d}"} for i in range(1,33)]}
        ]
        for change in cases:
            with self.subTest(change=str(change)[:70]):
                invalid=dict(baseline);invalid.update(change)
                with self.assertRaises(ValueError):
                    propose(y,invalid)
        with self.assertRaises(ValueError):
            propose(2,teacher_manifest(2))

if __name__=="__main__":
    unittest.main()
