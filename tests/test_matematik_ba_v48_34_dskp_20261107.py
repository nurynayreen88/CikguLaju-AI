"""Audit Year4 34 split-pair DSKP locators, distinguish provenance from teacher signoff."""
import csv
import unittest
from pathlib import Path
P=Path(__file__).resolve().parents[1]/"audits/matematik_v48_34_pasangan_T4_DSKP_20261107.csv"
class SplitPairEvidence(unittest.TestCase):
    def test_all_34_have_provenance_without_false_approval(self):
        with P.open(encoding="utf8",newline="") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),34)
        self.assertEqual(len({r["source_id"] for r in rows}),34)
        self.assertEqual({r["lesson_a"] for r in rows}&{r["lesson_b"] for r in rows},set())
        self.assertEqual(sum(r["source_issue_flag"]=="v48_CURRENCY_SIMULATION_CORRECTED" for r in rows),1)
        for r in rows:
            with self.subTest(source=r["source_id"]):
                self.assertIn("PDF",r["dskp_locator"])
                for c in r["sp_codes"].split(";"):
                    self.assertIn(c.strip()+":PDF",r["dskp_locator"])
                for k in ("A1_diff","A2_diff","PBD_diff","RPH_SP_present_both","dskp_SP_found"):
                    self.assertEqual(r[k],"YES")
                self.assertEqual(r["item_level_book_verified"],"NO")
                self.assertEqual(r["academic_signoff"],"PENDING")
                self.assertEqual(r["release_status"],"HOLD")
if __name__=="__main__":
    unittest.main()
