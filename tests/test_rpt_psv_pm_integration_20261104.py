"""Regression tests: PSV PDF, Moral cover, RPT menu isolation and paid access."""
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
from pypdf import PdfReader

from rpt_2027.psv import telegram_downloads as psv
from rpt_2027.english import telegram_downloads as english
from rpt_2027.pendidikan_moral import add_cover
from rpt_2027.pendidikan_moral import complete_96_downloads as moral_downloads
from rpt_2027.pendidikan_moral.complete_96_downloads import build_rpt_pdf, build_combined_rpt_pdf, combined_pdf_ready, source_rows as moral_rows

class PSVandMoralRPTTests(unittest.TestCase):
    def test_psv_source_and_pdf_five_years(self):
        self.assertFalse(psv.pdf_ready(1))
        self.assertFalse(psv.pdf_ready(9))
        self.assertEqual(psv.source_rows("3"), [])
        for year in range(2,7):
            rows=psv.source_rows(year)
            self.assertEqual(len(rows),42)
            self.assertEqual([r["PdP"] for r in rows],[f"{i:03d}" for i in range(1,43)])
            self.assertTrue(psv.pdf_ready(year))
            with TemporaryDirectory() as d:
                pdf=psv.build_pdf(year,Path(d)/f"psv_{year}.pdf")
                doc=PdfReader(str(pdf))
                self.assertGreaterEqual(len(doc.pages),2)
                self.assertIn("PENDIDIKAN SENI VISUAL",doc.pages[0].extract_text())
                self.assertIn(f"TAHUN {year}",doc.pages[0].extract_text())
                self.assertIn("042",doc.pages[-1].extract_text())
                self.assertGreater(doc.pages[0].mediabox.width,doc.pages[0].mediabox.height)
        with TemporaryDirectory() as d, patch.object(psv,"ROOT",Path(d)):
            self.assertEqual(psv.source_rows(2),[])
            self.assertFalse(psv.pdf_ready(2))

    def test_moral_cover_keeps_original_96_sessions(self):
        for group in ("A","B"):
            self.assertEqual(len(moral_rows(2,group)),96)
            with TemporaryDirectory() as d:
                content=build_rpt_pdf(2,group,Path(d)/"inner.pdf")
                original=PdfReader(str(content))
                final=add_cover.prepend_cover(2,group,content,Path(d)/"covered.pdf")
                pages=PdfReader(str(final))
                self.assertEqual(len(pages.pages),len(original.pages)+1)
                front=pages.pages[0].extract_text()
                self.assertIn("PENDIDIKAN MORAL TAHUN 2",front)
                self.assertIn(f"KUMPULAN {group}",front)
                self.assertIn("96 SESI",front)
                self.assertIn("096",pages.pages[-1].extract_text())
        with self.assertRaises(ValueError):
            add_cover.prepend_cover(2,"Z","missing.pdf","output.pdf")


    def test_combined_moral_one_pdf_contains_both_groups(self):
        for year in range(2,7):
            self.assertTrue(combined_pdf_ready(year))
            with TemporaryDirectory() as d:
                filename=Path(d)/f"moral_{year}.pdf"
                pdf=build_combined_rpt_pdf(year,filename)
                reader=PdfReader(str(pdf))
                self.assertEqual(len(reader.pages),29)
                self.assertIn(f"PENDIDIKAN MORAL TAHUN {year}",reader.pages[0].extract_text())
                self.assertIn("KUMPULAN A/B",reader.pages[0].extract_text())
                self.assertIn("KUMPULAN A",reader.pages[1].extract_text())
                self.assertIn("KUMPULAN B",reader.pages[15].extract_text())
                self.assertIn("096",reader.pages[14].extract_text())
                self.assertIn("096",reader.pages[28].extract_text())
        self.assertFalse(combined_pdf_ready(1))
        self.assertFalse(combined_pdf_ready(7))

    def test_moral_one_click_pdf_and_old_ab_callbacks(self):
        sent=[]
        state={"paid":False}
        def send(cid,msg,kb=None):
            sent.append(("message",msg,kb))
            return msg
        def send_document(cid,path,caption):
            file=Path(path)
            self.assertEqual(file.suffix,".pdf")
            self.assertEqual(len(PdfReader(str(file)).pages),29)
            self.assertIn("Kumpulan A dan B",caption)
            sent.append(("pdf",file.name,caption))
            return SimpleNamespace(ok=True,json=lambda:{"ok":True})
        ns={"callback":lambda cid,data:("original",data),"send":send,
            "send_document":send_document,
            "_access_info":lambda cid:{"active":state["paid"]},
            "_is_admin":lambda cid:False,
            "_telegram_delivery_ok_v25279":lambda result:result.ok}
        self.assertTrue(english.install(ns))
        self.assertTrue(moral_downloads.install(ns))
        ns["callback"](1,"rpt2027_pm_pdf_2")
        self.assertEqual(sent[-1][0],"message")
        self.assertIn("hanya untuk",sent[-1][1])
        self.assertFalse(any(x[0]=="pdf" for x in sent))
        state["paid"]=True
        ns["callback"](1,"rpt2027_year_2")
        menu=str(sent[-1][2])
        self.assertEqual(menu.count("rpt2027_pm_pdf_2"),1)
        self.assertNotIn("rpt2027_pm_96_a_2",menu)
        self.assertNotIn("rpt2027_pm_96_b_2",menu)
        self.assertNotIn("rpt2027_pm_rph54_docx_2",menu)
        for callback in ("rpt2027_pm_pdf_2","rpt2027_pm_96_a_2","rpt2027_pm_96_b_2"):
            ns["callback"](1,callback)
            self.assertEqual(sent[-1][0],"pdf")
            self.assertEqual(sent[-1][1],"RPT_Pendidikan_Moral_Tahun_2_2027.pdf")
        ns["callback"](1,"rpt2027_pm_pdf_9")
        self.assertEqual(sent[-1][0],"message")
        self.assertIn("tidak sah",sent[-1][1])
        self.assertEqual(ns["callback"](1,"other"),("original","other"))

    def test_paid_psv_and_legacy_callback_isolation(self):
        records=[]
        def send(cid,msg,buttons=None):
            records.append(("send",msg,buttons))
            return msg
        def send_document(cid,path,caption):
            file=Path(path)
            self.assertTrue(file.is_file())
            self.assertGreater(file.stat().st_size,8000)
            records.append(("document",caption,PdfReader(str(file)).pages[0].extract_text()))
            return SimpleNamespace(ok=True,json=lambda:{"ok":True})
        user={"paid":False}
        ns={
            "callback":lambda cid,data:("old",data),
            "send":send,"send_document":send_document,
            "_access_info":lambda cid:{"active":user["paid"]},
            "_is_admin":lambda cid:False,
            "_telegram_delivery_ok_v25279":lambda result:result.ok,
        }
        self.assertTrue(english.install(ns))
        self.assertEqual(ns["callback"](9,"rpt2027_pm_96_a_2"),("old","rpt2027_pm_96_a_2"))
        ns["callback"](9,"rpt2027_psv_pdf_2")
        self.assertEqual(records[-1][0],"send")
        self.assertIn("Akses Terhad",records[-1][1])
        user["paid"]=True
        ns["callback"](9,"rpt2027_year_2")
        menu=records[-1][2]
        names=str(menu)
        for required in ("rpt2027_psv_pdf_2","rpt2027_pm_pdf_2","rpt2027_en_pdf_2"):
            self.assertIn(required,names)
        for hidden in ("rpt2027_pm_96_a_2","rpt2027_pm_96_b_2","rpt2027_pm_rph54_pdf_2","rpt2027_pm_rph54_docx_2"):
            self.assertNotIn(hidden,names)
        ns["callback"](9,"rpt2027_psv_pdf_2")
        self.assertEqual(records[-1][0],"document")
        self.assertIn("Tahun 2",records[-1][1])
        self.assertIn("PENDIDIKAN SENI VISUAL",records[-1][2])
        ns["callback"](9,"rpt2027_psv_pdf_9")
        self.assertIn("tidak sah",records[-1][1])
        self.assertEqual(ns["callback"](9,"something_else"),("old","something_else"))

if __name__=="__main__":
    unittest.main()
