"""Semakan akademik berasaskan sumber untuk 4 pembetulan Matematik v50.

Lulus ujian ini bermaksud bukti pembetulan wujud; bukan kelulusan akademik 585 RPH.
"""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path
from rph_standalone.matematik import staging_preview_v50 as preview

ROOT = Path(__file__).resolve().parents[1] / "audits"

class V50SemanticEvidence(unittest.TestCase):
    def test_16_edits_from_four_lessons_and_no_formal_signoff(self):
        with (ROOT/"matematik_v50_4_rph_16_section_semantics_20261107.csv").open(
                encoding="utf-8",newline="") as handle:
            changes=list(csv.DictReader(handle))
        self.assertEqual(len(changes),16)
        self.assertEqual(Counter(x["lesson_id"] for x in changes),{
            "T2-L111":6,"T2-L112":6,"T4-L109":3,"T4-L114":1})
        for x in changes:
            with self.subTest(lesson=x["lesson_id"],section=x["section"]):
                self.assertNotEqual(x["old"],x["new"])
                self.assertEqual(x["teacher_signoff"],"PENDING")
                self.assertEqual(x["review_level"],"SOURCE_SCOPED_CONTENT_CORRECTION")
                self.assertIn("DSKP",x["source"])
                if x["lesson_id"] in ("T2-L111","T2-L112"):
                    self.assertNotIn("carta palang",x["new"].lower())
        self.assertTrue(any(
            x["lesson_id"]=="T2-L111" and x["section"]=="Rujukan"
            and "145–146" in x["new"] and "88–89" in x["new"]
            for x in changes
        ))
        self.assertTrue(any(
            x["lesson_id"]=="T4-L109" and x["section"]=="Aktiviti 1"
            and "membina piktograf" in x["new"] for x in changes))
        self.assertTrue(any(
            x["lesson_id"]=="T4-L109" and x["section"]=="Aktiviti 2"
            and "membina carta palang" in x["new"] for x in changes))
        self.assertTrue(any(
            x["lesson_id"]=="T4-L114"
            and "5 − 3 = 2 ikon" in x["new"]
            and "2 × 2 = 4 buku" in x["new"] for x in changes))

    def test_sha_pinned_manifest_does_not_claim_final_ready(self):
        data=json.loads((ROOT/"matematik_v50_release_gate_20261107.json").read_text(encoding="utf-8"))
        self.assertEqual(data["rph_total"],585)
        self.assertEqual(data["corrected_sections"],16)
        self.assertEqual(data["unchanged_individual_rph"],581)
        self.assertEqual(data["changed_word_pdf_markdown"],12)
        self.assertEqual(data["individual_pdf_a4_one_page"],585)
        self.assertEqual(data["academic_exercise_signoff"],0)
        self.assertFalse(data["real_telegram_web_staging_e2e"])
        self.assertFalse(data["school_calendar_2027_verified"])
        self.assertFalse(data["final_ready"])
        self.assertFalse(data["production_modified"])
        self.assertEqual(preview.EXPECTED_SHA256,data["sha256"])
        self.assertEqual(data["sha256"],"895c87161dd7b62d9cecdea20b1d9efdf7ce0b77a14915d4edc186c4d2c9cdbb")

if __name__=="__main__":
    unittest.main()
