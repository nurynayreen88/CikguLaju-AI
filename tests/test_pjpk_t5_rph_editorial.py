"""Editorial completeness checks for the three full T5 PK RPH drafts.

This validates source text structure, not teaching quality, A4 rendering or production readiness.
"""
import re
import unittest
from pathlib import Path

DOC = Path(__file__).resolve().parents[1] / "docs/pjpk/T5_PK_3_RPH_EDITORIAL_DRAFTS_20261024.md"
EXPECTED = {"2259": ("6.1", ("6.1.1", "6.1.2"), "88–89"),
            "2260": ("7.1", ("7.1.1", "7.1.2", "7.1.3"), "90–92"),
            "2261": ("8.1", ("8.1.1", "8.1.2", "8.1.3"), "96–100")}
SECTIONS = ("**Objektif:**", "**BBM:**", "**Pentaksiran:**", "**Set induksi:**",
            "**Aktiviti 1", "**Aktiviti 2", "**Pengukuhan/penilaian:**",
            "**Penutup:**", "**Rujukan:**", "**Buku teks:**")

class RPHEditorialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        text = DOC.read_text(encoding="utf-8")
        chunks = re.split(r"(?=^## (?:2259|2260|2261) — )", text, flags=re.M)
        cls.blocks = {m.group(1): chunk for chunk in chunks
                      if (m := re.match(r"## (2259|2260|2261) — ", chunk))}
    def test_all_three_complete_drafts_exist(self):
        self.assertEqual(set(self.blocks), set(EXPECTED))
    def test_each_draft_has_full_rph_sections(self):
        for ident, block in self.blocks.items():
            with self.subTest(ident=ident):
                for section in SECTIONS:
                    self.assertIn(section, block)
                self.assertGreater(len(block), 1200)
    def test_sp_and_textbook_reference_per_draft(self):
        for ident, (sk, sp_codes, pages) in EXPECTED.items():
            block = self.blocks[ident]
            with self.subTest(ident=ident):
                self.assertIn(f"**SK {sk}:**", block)
                for sp in sp_codes:
                    self.assertIn(f"**SP {sp}:**", block)
                self.assertIn(pages, block)
    def test_drafts_not_misrepresented_as_production(self):
        text = DOC.read_text(encoding="utf-8")
        self.assertIn("NOT PRODUCTION READY", text)
        self.assertIn("production_ready=0", text)

if __name__ == "__main__":
    unittest.main()
