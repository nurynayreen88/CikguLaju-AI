"""RPH Matematik v53: 47 targeted teaching/BA changes, explicitly never RPT."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path
from rph_standalone.matematik import staging_preview_v53 as preview

A=Path(__file__).resolve().parents[1]/"audits"

class V53RPHOnly(unittest.TestCase):
    def test_47_changes_in_32_lessons_no_rpt(self):
        with (A/"matematik_v53_47_pembetulan_RPH_sahaja_20261107.csv").open(encoding="utf8",newline="") as f:
            data=list(csv.DictReader(f))
        self.assertEqual(len(data),47)
        self.assertEqual(len({x["id"] for x in data}),32)
        self.assertEqual(Counter(x["section"] for x in data),{
            "Set induksi (5 minit)":13,
            "Aktiviti 2 — Aplikasi/Latihan (20 minit)":21,
            "Aktiviti 3 — Buku Aktiviti/PBD (10 minit)":13})
        for x in data:
            with self.subTest(lesson=x["id"],section=x["section"]):
                self.assertNotEqual(x["before"],x["after"])
                self.assertEqual(x["review"],"source_scoped_editorial_not_formal_approval")
                self.assertNotIn("RPT",x["source"])
                if x["section"]=="Aktiviti 2 — Aplikasi/Latihan (20 minit)":
                    self.assertNotIn("nombor berbeza dalam had SP",x["after"])
                if x["section"]=="Aktiviti 3 — Buku Aktiviti/PBD (10 minit)":
                    self.assertIn("Buku Aktiviti",x["after"])
        self.assertEqual(sum(x["section"]=="Aktiviti 3 — Buku Aktiviti/PBD (10 minit)" and
                             x["year"]=="2" for x in data),5)
        self.assertEqual(sum(x["section"]=="Aktiviti 3 — Buku Aktiviti/PBD (10 minit)" and
                             x["year"]=="3" for x in data),8)

    def test_archive_staging_release_held(self):
        gate=json.loads((A/"matematik_v53_release_gate_RPH_only_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["changed_lessons_count"],32)
        self.assertEqual(gate["changed_sections"],47)
        self.assertEqual(gate["unchanged_lessons_count"],553)
        self.assertEqual(gate["individual_pdf_a4_onepage_count"],585)
        self.assertEqual(gate["combined_pdf_count"],5)
        self.assertEqual(gate["visually_checked_BA_page_specific_lessons"],13)
        self.assertEqual(preview.EXPECTED_SHA256,gate["archive_sha256"])
        self.assertEqual(gate["academic_exercise_item_teacher_signoff_count"],0)
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
        self.assertFalse(gate["rpt_changed"])
        self.assertFalse(gate["telegram_web_real_staging_e2e"])
        self.assertNotIn("RPT",gate["archive_name"])
if __name__=="__main__":
    unittest.main()
