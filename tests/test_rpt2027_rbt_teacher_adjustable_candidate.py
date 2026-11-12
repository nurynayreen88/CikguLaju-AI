"""Teacher-adjustable RBT 2027 RPT defaults preserve all original data."""
import unittest
import tempfile
from pathlib import Path
from scripts.build_rpt_2027_rbt_teacher_adjustable_candidate import (
    rbt_teacher_adjustable_plan,build_all
)
from scripts.build_rpt_2027_standard_preview import rbt_records
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

class RBTTeacherAdjustableCandidateQA(unittest.TestCase):
    def test_32_week_2027_source_calendar_and_nondestructive(self):
        weeks=load_calendar_weeks()
        for year in (4,5,6):
            old=rbt_records(year)
            new=rbt_teacher_adjustable_plan(year)
            self.assertEqual(len(old),32)
            self.assertEqual(len(new),32)
            self.assertTrue(all(not r["week"] for r in old))
            self.assertEqual([r["id"] for r in old],[r["id"] for r in new])
            for i,row in enumerate(new,3):
                w=f"M{i:02d}"
                self.assertEqual(row["week"],w+" (CADANGAN RPT)")
                self.assertEqual((row["a_start"],row["a_end"]),weeks["A"][w])
                self.assertEqual((row["b_start"],row["b_end"]),weeks["B"][w])
                self.assertIn("CADANGAN RPT",row["note"])
                self.assertIn("bukan tarikh kelas sebenar",row["note"])
                self.assertEqual(row["schedule_status"],
                    "DEFAULT_2027_TEACHER_ADJUSTABLE_CANDIDATE_NOT_APPROVED")
    def test_three_PDF_candidates_separate_from_56_main_drafts(self):
        with tempfile.TemporaryDirectory() as work:
            out=build_all(Path(work))
            self.assertEqual([(y,n) for y,n,_ in out],[(4,32),(5,32),(6,32)])
            for _,_,file in out:
                self.assertIn("DRAF",file.name)
                self.assertTrue(file.exists())
                self.assertGreater(file.stat().st_size,5000)
if __name__=="__main__":
    unittest.main()
