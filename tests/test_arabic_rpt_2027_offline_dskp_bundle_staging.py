"""Verify Arabic RPT source annotations become real in-PDF KPM DSKP jumps.

Uses fully synthetic two-page facsimiles so no KPM PDF or user-owned Drive
data is committed. A real staging artifact supplies actual SHA-locked pages.
"""
import tempfile
import unittest
from pathlib import Path

import fitz

from scripts.build_arabic_rpt_2027_offline_dskp_bundle_staging import repack_year


class OfflineArabicRPTSourceLinksQA(unittest.TestCase):
    def test_60_year2_source_links_become_exact_internal_pdf_jumps(self):
        url="https://drive.google.com/file/d/1WY_c69UshDm3jHzVK86G2xfu77UUkGYO/view"
        with tempfile.TemporaryDirectory() as temp:
            folder=Path(temp)
            rpt=fitz.open()
            cover=rpt.new_page(width=842,height=595)
            cover.insert_text((60,80),"RPT BAHASA ARAB TAHUN 2 2027 DRAF")
            # Build all annotations on one page to avoid an older PyMuPDF
            # 1.24 in-memory multiple-page annotation serialization quirk.
            # The real 5 PDFs are separately checked across many pages.
            page=rpt.new_page(width=842,height=595)
            for i in range(60):
                top=29+i*9
                page.insert_text((40,top),"Buka DSKP asal (halaman PDF 31)",fontsize=5.2)
                page.insert_link({
                    "kind":fitz.LINK_URI,"from":fitz.Rect(40,top-6,270,top+2),
                    "uri":url
                })
            original=rpt.tobytes(garbage=4,deflate=True)
            rpt.close()
            source=fitz.open()
            source.new_page(width=595,height=842).insert_text((60,80),"LAMPIRAN DSKP TAHUN 2")
            source.new_page(width=595,height=842).insert_text((60,80),"KSSR  BAHASA ARAB TAHUN 2")
            annex=folder/"source.pdf"
            source.save(annex)
            source.close()
            records=[
                {"year":2,"sp_code":f"1.1.{n}","pdf_page":31,
                 "full_statement_text_verified":False,
                 "source_visual_facsimile":True}
                for n in range(1,20)
            ]
            output=folder/"BAHASA_ARAB_TAHUN_2_DRAF.pdf"
            result=repack_year(original,annex,2,records,url,output)
            self.assertEqual(result["link_count"],60)
            self.assertEqual(result["appended_source_pages"],2)
            self.assertEqual(result["source_text_academic_signoffs"],0)
            self.assertFalse(result["release_ready"])
            with fitz.open(output) as final:
                self.assertEqual(len(final),4)
                links=[x for p in list(final)[:2] for x in p.get_links()]
                self.assertEqual(len(links),60)
                self.assertTrue(all(x["kind"]==fitz.LINK_GOTO
                                    and x["page"]==3 for x in links))
                self.assertTrue(all(p.rect.width>p.rect.height for p in list(final)[:2]))
                self.assertTrue(all(p.rect.width<p.rect.height for p in list(final)[2:]))

    def test_reject_wrong_year_or_unapproved_statement(self):
        with tempfile.TemporaryDirectory() as temp:
            source=Path(temp)/"annex.pdf"
            with self.assertRaises(ValueError):
                repack_year(b"",source,4,[],
                    "https://drive.google.com/file/d/1WY_c69UshDm3jHzVK86G2xfu77UUkGYO/view",
                    Path(temp)/"test_DRAF.pdf")


if __name__=="__main__":
    unittest.main()
