"""Six PI 2027 held lessons: five optional sourced tasmi notes, one blocked conflict."""
import json
import unittest
from pathlib import Path
from collections import Counter

from scripts.build_rpt_2027_remaining_four_subjects_staging import pi_records
from rpt_2027.common.calendar_week_mapping_staging import load_calendar_weeks

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/pendidikan_islam_rpt2027_6_held_source_recovery_20261107_DRAF.json"
EXPECTED={(2,35):"M14",(6,6):"M03",(6,14):"M05",
          (6,18):"M06",(6,60):"M18",(6,117):"M36"}

class PIHeldRecoveredSourceEvidenceQA(unittest.TestCase):
    def test_recovered_sourced_week_for_all_six_while_original_rph_remains_held(self):
        data=json.loads(LEDGER.read_text(encoding="utf-8"))
        self.assertEqual(data["status"],"PROVISIONAL_SOURCE_RECOVERY_FOR_HELD_PI_RPT_PREVIEW_ONLY")
        self.assertEqual(data["source_rph_held_count"],6)
        self.assertEqual(data["optional_tasmi_source_rows"],5)
        self.assertEqual(data["conflicting_ibaadah_source_rows"],1)
        self.assertEqual(data["release_ready_count"],0)
        self.assertEqual(data["production_changes"],0)
        items={(x["year"],x["lesson"]):x for x in data["entries"]}
        self.assertEqual(set(items),set(EXPECTED))
        self.assertEqual(Counter(x["kind"] for x in items.values()),{
            "KHATAM_TASMI_OPTIONAL_NO_OFFICIAL_SK_SP_IN_SOURCE":5,
            "IBADAH_2026_RPT_STANDARD_CONFLICT_HOLD":1,
        })
        weeks=load_calendar_weeks()
        for year in (2,6):
            source=json.loads((ROOT/f"rph_standalone/pendidikan_islam_draf_2027/year{year}.json").read_text("utf-8"))
            originals={r["lesson"]:r for r in source["records"]}
            previews=pi_records(year)
            for (y,lesson),item in items.items():
                if y!=year:
                    continue
                with self.subTest(year=year,lesson=lesson):
                    original=originals[lesson]
                    self.assertTrue(original["withheld"])
                    self.assertFalse(original.get("fields"))
                    self.assertFalse(original.get("verified_ready"))
                    p=previews[lesson-1]
                    self.assertTrue(p["source_held"])
                    self.assertFalse(p["held_release_approved"])
                    self.assertEqual(p["week"],EXPECTED[(year,lesson)])
                    self.assertEqual((p["a_start"],p["a_end"]),weeks["A"][p["week"]])
                    self.assertEqual((p["b_start"],p["b_end"]),weeks["B"][p["week"]])
                    self.assertIn("REKOD DITAHAN",p["note"])
                    self.assertFalse(p["held_release_approved"])
                    if item["kind"].startswith("KHATAM"):
                        self.assertFalse(item["source_sk_sp_given"])
                        self.assertIn("tasmi",p["topic"].lower())
                        self.assertIn("BUKAN KOD SK RASMI",p["sk"])
                        self.assertIn("TIADA KOD SP RASMI",p["sp"])
                    else:
                        self.assertTrue(item["source_conflict"])
                        self.assertIn("KONFLIK",p["topic"])
                        self.assertIn("4.2 — Solat Ketika Sakit",p["sk"])
                        for code in ("4.2.3","4.2.4","4.2.5"):
                            self.assertIn(code,p["sp"])
                        self.assertIn("L059",p["note"])

if __name__=="__main__":
    unittest.main()
