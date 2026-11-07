"""Evidence-level DSKP correction for Year 6 8.1.1 — do not confuse 45° with 450."""
import csv
import json
import unittest
from pathlib import Path

AUDIT = Path(__file__).resolve().parents[1] / "audits"

class MathematicsV46DegreeCorrection(unittest.TestCase):
    def test_exactly_two_source_grounded_lessons(self):
        with (AUDIT / "matematik_v46_2_degree_symbol_fixes_20261107.csv").open(
            encoding="utf-8", newline=""
        ) as file:
            rows = list(csv.DictReader(file))
        self.assertEqual({r["lesson_id"] for r in rows},{"T6-L108","T6-L109"})
        self.assertEqual(len(rows),2)
        for row in rows:
            self.assertEqual(row["sp_code"],"8.1.1")
            self.assertEqual(row["wrong_form"],"450; 900; 1800")
            self.assertEqual(row["correct_form"],"45°; 90°; 180°")
            self.assertEqual(row["error_type"],"DEGREE_SYMBOL_OMITTED")
            for key in ("word_corrected","pdf_corrected","markdown_corrected","merged_pdf_regenerated"):
                self.assertEqual(row[key],"YES")
            self.assertEqual(row["academic_final_ready"],"NO")

    def test_release_gate_requires_real_staging_and_academic_signoff(self):
        gate=json.loads((AUDIT/"matematik_v46_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["version"],"v46")
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["corrected_lesson_ids"],["T6-L108","T6-L109"])
        self.assertEqual(gate["QA_one_page_A4"],585)
        self.assertEqual(gate["QA_bold_phases"],585)
        self.assertEqual(gate["BA_Y2_Y3_effective_references"],234)
        self.assertEqual(gate["academic_exercise_approval_count"],0)
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["real_staging_E2E_tested"])
        self.assertFalse(gate["production_modified"])
        self.assertEqual(len(gate["sha256"]),64)

if __name__=="__main__":
    unittest.main()
