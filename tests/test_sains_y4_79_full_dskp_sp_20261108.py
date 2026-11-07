"""79/79 Year4 Science official DSKP SP statements in actual Word/PDF."""
from __future__ import annotations

import unittest
from docx import Document
from pypdf import PdfReader

from tools.render_sains_y4_79_rph_draf_20261107 import get_y4_records,OUT
from tools.sains_y4_79_official_sp_statements_20261108 import checked_statements
from web.sains_rph_quality_release_gate_20261108 import approved_count


def normal(s):
    return "".join(str(s).casefold().split())


class TestYear4FullDSKPText(unittest.TestCase):
    def test_all_79_official_sp_statements_have_exact_source_and_hold(self):
        original=checked_statements()
        rows=get_y4_records()
        self.assertEqual(len(original),79)
        self.assertEqual(len(rows),79)
        self.assertEqual(set(original),{r["sp"] for r in rows})
        self.assertEqual(approved_count(),0)
        for r in rows:
            self.assertEqual(original[r["sp"]]["sp_text"],r["sp_full_text"])
            self.assertEqual(original[r["sp"]]["sk"],r["sk"])
            self.assertEqual(r["status"],"DRAF_HOLD")
            self.assertIsNone(r["textbook_pages"])
            self.assertIsNone(r["curriculum_quality_percent"])

    def test_all_79_real_word_and_pdf_show_official_sp_with_single_a4(self):
        for r in get_y4_records():
            stem=f"SAINS_T4_PDP_{int(r['pdp_number']):03d}_DRAF"
            sp=r["sp"];sentence=r["sp_full_text"]
            word=Document(str(OUT/(stem+".docx")))
            self.assertEqual(len(word.tables),2)
            texts=" ".join(cell.text for tb in word.tables for tr in tb.rows for cell in tr.cells)
            self.assertIn(normal(sp),normal(texts))
            self.assertIn(normal(sentence),normal(texts),(sp,"word"))
            pdf=PdfReader(str(OUT/(stem+".pdf")))
            self.assertEqual(len(pdf.pages),1,sp)
            page=pdf.pages[0]
            self.assertAlmostEqual(float(page.mediabox.width),595.28,delta=2)
            self.assertAlmostEqual(float(page.mediabox.height),841.89,delta=2)
            extracted=page.extract_text()
            self.assertIn(normal(sp),normal(extracted))
            self.assertIn(normal(sentence),normal(extracted),(sp,"pdf"))
            self.assertIn("DRAF",extracted)


if __name__=="__main__":
    unittest.main()
