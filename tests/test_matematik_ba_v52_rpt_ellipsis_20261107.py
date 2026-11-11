"""Track textual truncation in provisional Mathematics RPT 2027 PDFs (source snapshot v28)."""
import csv
import json
import unittest
from collections import Counter
from pathlib import Path

AUDITS=Path(__file__).resolve().parents[1]/"audits"

class V52RPTTextCompleteness(unittest.TestCase):
    def test_210_source_ellipsis_not_confused_with_sp_code_matching(self):
        with (AUDITS/"matematik_v52_rpt2027_teks_terpotong_20261107.csv").open(
                newline="",encoding="utf8") as f:
            rows=list(csv.DictReader(f))
        self.assertEqual(len(rows),210)
        self.assertEqual(Counter(x["year"] for x in rows),{
            "3":35,"4":71,"5":50,"6":54})
        for x in rows:
            self.assertTrue("…" in x["context"] or "..." in x["context"])
            self.assertGreater(int(x["page"]),0)

    def test_release_held_while_rpt_text_not_complete(self):
        gate=json.loads((AUDITS/"matematik_v52_release_gate_20261107.json").read_text(encoding="utf8"))
        self.assertEqual(gate["rpt_v28_total_ellipsis_occurrences"],210)
        self.assertEqual(gate["rpt_2027_sp_and_lesson_matches"],585)
        self.assertFalse(gate["rpt_full_sp_descriptions_and_focus_reviewed"])
        self.assertFalse(gate["final_ready"])

if __name__=="__main__":
    unittest.main()
