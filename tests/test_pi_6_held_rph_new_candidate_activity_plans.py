"""Six PI held sources now have detailed proposals, without inventing official SP."""
import json
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/pendidikan_islam_6_held_rph_new_candidate_activity_plans_20261107.json"

class PI6HeldRPHNewCandidatesQA(unittest.TestCase):
    def test_six_source_proposals_complete_without_releasing_v5(self):
        a=json.loads(LEDGER.read_text("utf-8"))
        self.assertEqual(a["status"],"STAGING_RPH_6_NEW_SOURCE_GROUNDED_CANDIDATES_NOT_V5_REPLACEMENT")
        self.assertEqual(len(a["records"]),6)
        self.assertTrue(a["held_original_records_still_held"])
        self.assertEqual(a["tasmi_no_official_sp"],5)
        self.assertEqual(a["source_year6_ibadah_corrected"],1)
        self.assertEqual(a["approval_count"],0)
        self.assertFalse(a["release_ready"])
        self.assertEqual(a["production_changes"],0)
        self.assertEqual({(i["year"],i["lesson"]) for i in a["records"]},
                         {(2,35),(6,6),(6,14),(6,18),(6,60),(6,117)})
        for y in (2,6):
            source=json.loads((ROOT/f"rph_standalone/pendidikan_islam_draf_2027/year{y}.json").read_text("utf-8"))
            originals={r["lesson"]:r for r in source["records"]}
            for row in (r for r in a["records"] if r["year"]==y):
                self.assertTrue(originals[row["lesson"]]["withheld"])
                for field in ("objectives","teacher","students","assessment"):
                    self.assertGreater(len(row[field]),20)
                self.assertGreater(len(row["src"]),10)
                if row["lesson"]!=60:
                    self.assertIsNone(row["sk"])
                    self.assertEqual(row["sp"],[])
                else:
                    self.assertEqual(row["sk"],"4.2")
                    self.assertEqual(row["sp"],["4.2.3","4.2.4","4.2.5"])
                    self.assertIn("Solat Ketika Sakit",row["note"])
                    self.assertIn("L059",row["note"])
        last=next(x for x in a["records"] if x["lesson"]==117)
        self.assertIn("NOT Juz 29",last["note"])

if __name__=="__main__":unittest.main()
