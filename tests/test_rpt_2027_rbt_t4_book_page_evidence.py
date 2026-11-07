"""RBT T4: 32 per-PdP RPH/CSV references agree with original textbook ledger.

Requires only repository files. Separate direct-PDF verification is recorded
in the dated audit, and is NOT equivalent to visual/pedagogical approval.
"""
from __future__ import annotations
import json
import re
import unittest
from pathlib import Path

from rpt_2027.rbt.pdf_runtime import source_rows

ROOT = Path(__file__).resolve().parents[1]


class RBTYear4BookPageEvidenceQA(unittest.TestCase):
    def test_all_32_rph_page_lists_match_57_book_standard_codes(self):
        ledger = json.loads((ROOT / "audits/rbt_t4_textbook_sp_page_map_20261106.json"
                             ).read_text(encoding="utf-8"))
        rph = json.loads((ROOT / "rph_standalone/rbt/tahun_4/RPH_RBT_T4_2027_DRAF.json"
                          ).read_text(encoding="utf-8"))
        standards = ledger["sp_printed_page_index"]
        rows = source_rows(4)
        lessons = rph["pelajaran"]
        self.assertEqual(len(standards), 57)
        self.assertEqual(len(rows), len(lessons))
        self.assertEqual(len(rows), 32)
        self.assertEqual(ledger["visual_lesson_approvals"], 0)
        for i, (row, lesson) in enumerate(zip(rows, lessons), 1):
            with self.subTest(pdp=i):
                self.assertEqual(int(row["PdP"]), lesson["pdp"])
                self.assertEqual(row["ID"], lesson["id"])
                self.assertEqual(row["SP"].split(" / "), lesson["sp_codes"])
                pages = sorted(set(p for code in lesson["sp_codes"]
                                   for p in standards[code]))
                self.assertEqual(
                    pages,
                    sorted(set(lesson["rujukan_buku_teks"][
                        "calon_muka_surat_teks_digital"]))
                )
                candidate = row["Rujukan Buku Teks m/s"]
                pattern = r"^(\d+(?:,\s*\d+)*) \(calon teks digital; belum sah\)$"
                found = re.fullmatch(pattern, candidate)
                self.assertIsNotNone(found)
                self.assertEqual(
                    pages, sorted(set(int(s.strip()) for s in found.group(1).split(",")))
                )
                self.assertIsNone(lesson["rujukan_buku_teks"]["muka_surat"])
                self.assertIsNone(lesson["rujukan_buku_teks"]["aktiviti_buku_teks"])
                self.assertFalse(lesson["review"]["release_ready"])
                self.assertFalse(lesson["review"]["halaman_buku_disahkan"])


if __name__ == "__main__":
    unittest.main()
