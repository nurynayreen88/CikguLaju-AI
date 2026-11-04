"""Isolated RPT PJPK 2027 PDF and Telegram entitlement tests."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch

from rpt_2027.pjpk import telegram_downloads as pjpk


class PJPKRPT2027Tests(unittest.TestCase):
    def test_all_five_year_pdf_assets_are_local_and_valid(self):
        for year in range(2, 7):
            with self.subTest(year=year):
                self.assertTrue(pjpk.pdf_ready(year))
                self.assertGreater(pjpk.pdf_path(year).stat().st_size, 50000)
                self.assertTrue(pjpk.pdf_path(year).name.endswith("_DRAF.pdf"))
        with self.assertRaises(ValueError):
            pjpk.pdf_path(1)
        self.assertFalse(pjpk.pdf_ready("2"))

    def test_manifest_is_readonly_and_statuses_are_draft(self):
        data=json.loads((pjpk.PDF_ROOT/"pjpk_2027_rpt_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(len(data["records"]), 339)
        self.assertEqual(len(data["weeks"]), 38)
        self.assertFalse(data["ready"])
        self.assertTrue(all(x["ready"] is False for x in data["records"]))
        byyear={y:sum(1 for x in data["records"] if x["year"]==y) for y in range(2,7)}
        self.assertEqual(byyear,{2:72,3:70,4:66,5:65,6:66})
        blocked=[x for x in data["records"] if x["status"].startswith("BLOK")]
        self.assertEqual(len(blocked), 1)
        self.assertEqual((blocked[0]["year"],blocked[0]["subject"],blocked[0]["pdp"]),(6,"PJ",33))

    def test_paid_and_admin_download_only_exact_year_and_preserve_other_callbacks(self):
        sent=[]; docs=[]; previous=[]
        def cb(cid,data):
            previous.append((cid,data))
            return "previous"
        ns={
            "callback":cb,
            "send":lambda *args: sent.append(args) or "message",
            "send_document":lambda *args: docs.append(args) or "delivered",
            "_access_info":lambda cid: {"active": cid==2},
            "_is_admin":lambda cid: cid==1,
            "_telegram_delivery_ok_v25279":lambda result:result=="delivered",
        }
        self.assertTrue(pjpk.install(ns))
        self.assertTrue(ns["CIKGULAJU_RPT_PJPK_2027_INSTALLED"])
        self.assertEqual(ns["callback"](9,"rpt2027_home"),"previous")
        self.assertEqual(previous,[(9,"rpt2027_home")])
        self.assertEqual(ns["callback"](9,"rpt2027_pjpk_pdf_3"),"message")
        self.assertEqual(len(docs),0)
        self.assertEqual(ns["callback"](1,"rpt2027_pjpk_pdf_1"),"message")
        self.assertEqual(len(docs),0)
        for cid,year in ((1,2),(2,6)):
            self.assertEqual(ns["callback"](cid,f"rpt2027_pjpk_pdf_{year}"),"delivered")
            self.assertEqual(docs[-1][1],str(pjpk.pdf_path(year)))
            self.assertIn("DRAF",docs[-1][2])
        self.assertTrue(pjpk.install(ns))

    def test_missing_asset_fails_closed_and_never_sends_2016_or_other_year(self):
        msgs=[];docs=[]
        ns={"callback":lambda *_:"old","send":lambda *args:msgs.append(args) or "notice",
            "send_document":lambda *args:docs.append(args),
            "_access_info":lambda cid:{"active":True},"_is_admin":lambda cid:False}
        self.assertTrue(pjpk.install(ns))
        with patch.object(pjpk,"pdf_ready",return_value=False):
            self.assertEqual(ns["callback"](1,"rpt2027_pjpk_pdf_4"),"notice")
        self.assertFalse(docs)
        self.assertIn("Tahun 4",msgs[-1][1])

    def test_english_menu_contains_pjpk_button_without_touching_other_subjects(self):
        from rpt_2027.english import telegram_downloads as english
        sent=[]
        ns={"callback":lambda *_:"old","send":lambda *a:sent.append(a) or "ok",
            "send_document":lambda *_:"ok","_access_info":lambda *_:{"active":True},
            "_is_admin":lambda *_:False}
        self.assertTrue(english.install(ns))
        self.assertEqual(ns["callback"](23,"rpt2027_year_2"),"ok")
        buttons=[b["callback_data"] for row in sent[-1][2] for b in row]
        self.assertIn("rpt2027_pjpk_pdf_2",buttons)
        self.assertIn("rpt2027_en_pdf_2",buttons)
        self.assertIn("rpt2027_home",buttons)


if __name__=="__main__":
    unittest.main()
