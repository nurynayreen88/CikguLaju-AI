"""Matematik v52 staging audit: source-grounded SP ratio and fraction competencies.

This validates the audited change ledger and release restrictions. It does NOT
mark textbook exercise-level teacher signoff complete.
"""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path
from rph_standalone.matematik import staging_preview_v52 as preview

ROOT=Path(__file__).resolve().parents[1]/"audits"

class V52SourceCompetencyAudit(unittest.TestCase):
    def test_13_rph_with_42_traceable_edits(self):
        with (ROOT/"matematik_v52_13_rph_komponen_SP_20261107.csv").open(
            encoding="utf-8",newline=""
        ) as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),42)
        self.assertEqual(len({x["lesson_id"] for x in rows}),13)
        self.assertEqual(Counter({k:len([x for x in rows if x["lesson_id"]==k]) for k in {x["lesson_id"] for x in rows}}).total(),13)
        self.assertEqual({x["lesson_id"] for x in rows},{
            "T4-L104","T5-L072","T5-L074","T5-L077","T5-L079","T5-L082",
            "T5-L089","T5-L090","T5-L091","T5-L092","T5-L093","T5-L107","T5-L108"
        })
        for x in rows:
            with self.subTest(lesson=x["lesson_id"],section=x["section"]):
                self.assertNotEqual(x["before"],x["after"])
                self.assertIn("DSKP Matematik Tahun",x["DSKP_source"])
                self.assertEqual(x["formal_teacher_signoff"],"PENDING")

    def test_truncated_ratio_sp_completed_as_source_actual(self):
        with (ROOT/"matematik_v52_13_rph_komponen_SP_20261107.csv").open(
            encoding="utf8",newline=""
        ) as f:
            rows=list(csv.DictReader(f))
        defs={(x["lesson_id"],x["section"]):x["after"] for x in rows}
        self.assertIn("1:1 hingga 1:10, 1:100 dan 1:1000",defs["T4-L104","SP"])
        for lesson in ("T5-L107","T5-L108"):
            sp=defs[lesson,"SP"]
            for phrase in ("a : b","bahagian kepada bahagian",
                           "bahagian kepada keseluruhan","keseluruhan kepada bahagian"):
                self.assertIn(phrase,sp)
            self.assertIn("bahagian:keseluruhan",defs[lesson,"Pengukuhan/Pentaksiran"] if lesson=="T5-L107" else defs[lesson,"Aktiviti 2"]+" "+defs[lesson,"Pengukuhan/Pentaksiran"]) if lesson=="T5-L107" else self.assertIn("ketiga-tiga hubungan",defs[lesson,"Pengukuhan/Pentaksiran"])

    def test_fraction_content_and_pbd_added_to_both_skill_families(self):
        with (ROOT/"matematik_v52_13_rph_komponen_SP_20261107.csv").open(
            encoding="utf8",newline=""
        ) as f:
            rows=list(csv.DictReader(f))
        for lesson in ("T5-L072","T5-L074","T5-L077","T5-L079","T5-L082",
                       "T5-L089","T5-L090","T5-L091","T5-L092","T5-L093"):
            new={x["section"]:x["after"] for x in rows if x["lesson_id"]==lesson}
            self.assertIn("pecahan",new["Pengukuhan/Pentaksiran"],lesson)
            self.assertIn("/",new["Aktiviti 2"],lesson)

    def test_release_gate_fails_closed(self):
        gate=json.loads((ROOT/"matematik_v52_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["rph_total"],585)
        self.assertEqual(gate["changed_sections"],42)
        self.assertEqual(gate["unchanged_rph_count"],572)
        self.assertEqual(gate["individual_pdf_a4_onepage"],585)
        self.assertEqual(gate["year2_3_BA_reference_count"],234)
        self.assertEqual(gate["rpt_2027_sp_and_lesson_matches"],585)
        self.assertEqual(gate["formal_academic_signoff"],0)
        self.assertFalse(gate["all_textbook_exercises_reviewed"])
        self.assertFalse(gate["telegram_web_real_staging_e2e"])
        self.assertFalse(gate["final_ready"])
        self.assertFalse(gate["production_modified"])
        self.assertEqual(preview.EXPECTED_SHA256,gate["sha256"])

if __name__=="__main__":
    unittest.main()
