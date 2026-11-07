"""v45 opt-in staging preview: synthetic, no Telegram/DB calls or real ZIP required."""
import hashlib
import json
import os
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from rph_standalone.matematik import staging_preview_v45 as m


class GoodReply:
    ok=True
    def json(self):return {"ok":True}


class PreviewV45(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix="math_v45_stage_")
        cls.path=Path(cls.temp.name)/"stage.zip"
        with zipfile.ZipFile(cls.path,"w",compression=zipfile.ZIP_DEFLATED) as z:
            for year in range(2,7):
                for n in range(1,118):
                    for folder,fmt,head in (("PDF","pdf",b"%PDF-1.7\n"),
                                            ("Word","docx",b"PK\\x03\\x04".decode("unicode_escape").encode("latin1")),
                                            ("Markdown","md",b"# RPH\n")):
                        z.writestr(f"Tahun_{year}/{folder}/lesson_{n:03}.{fmt}",
                                   head + f"year={year} lesson={n}\n".encode()+b"A"*600)
            z.writestr("AUDIT/V45_RELEASE_GATE.json",json.dumps({
                "rph_total":585,"BA_Y2_Y3_effective_references":234,"final_ready":False
            }))
        cls.sha=hashlib.sha256(cls.path.read_bytes()).hexdigest()
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()

    def setUp(self):
        self.sent=[];self.messages=[];self.access=False;self.admin=False
        self.ns={
            "callback":lambda chat,data:("old",chat,data),
            "send":lambda chat,msg:self.messages.append(msg) or msg,
            "send_document":lambda chat,path,cap:self.sent.append((chat,Path(path).read_bytes(),cap)) or GoodReply(),
            "_access_info":lambda chat:{"active":self.access},
            "_is_admin":lambda chat:self.admin,
        }
        self.old_sha=m.EXPECTED_SHA256
        m.EXPECTED_SHA256=self.sha
    def tearDown(self):m.EXPECTED_SHA256=self.old_sha

    def test_archive_gate_requires_585_and_234(self):
        self.assertEqual(m.verify_archive(self.path,self.sha),self.path)
        self.assertTrue(m.extract_rph_bytes(self.path,3,61,"pdf",self.sha).startswith(b"%PDF-"))
        with self.assertRaises(m.PreviewUnavailable):
            m.verify_archive(self.path,"0"*64)

    def test_disabled_unless_staging_and_opt_in(self):
        with patch.dict(os.environ,{},clear=True):
            self.assertFalse(m.install(self.ns,self.path))
        with patch.dict(os.environ,{m.STAGING_FLAG:"1","CIKGULAJU_ENVIRONMENT":"production"},clear=True):
            self.assertFalse(m.install(self.ns,self.path))

    def test_authorized_preview_and_nonpreview_passthrough(self):
        self.access=True
        with patch.dict(os.environ,{m.STAGING_FLAG:"1","CIKGULAJU_ENVIRONMENT":"staging"},clear=True):
            self.assertTrue(m.install(self.ns,self.path))
        self.assertEqual(self.ns["callback"](101,"home"),("old",101,"home"))
        r=self.ns["callback"](101,"mathrph_v45_preview_y2_l001_pdf")
        self.assertTrue(r.ok)
        self.assertEqual(len(self.sent),1)
        self.assertIn("v45",self.sent[0][2])

    def test_unpaid_and_forged_callback_fail_closed(self):
        with patch.dict(os.environ,{m.STAGING_FLAG:"1","CIKGULAJU_ENVIRONMENT":"staging"},clear=True):
            self.assertTrue(m.install(self.ns,self.path))
        self.ns["callback"](3,"mathrph_v45_preview_y2_l001_pdf")
        self.assertEqual(len(self.sent),0)
        self.ns["callback"](3,"mathrph_v45_preview_y2_l999_pdf")
        self.assertEqual(len(self.sent),0)

    def test_no_trial_db_payment_effect(self):
        self.admin=True
        self.ns["deduct_trial"]=lambda *a,**k:self.fail("trial must not change")
        self.ns["_sb_request"]=lambda *a,**k:self.fail("DB must not be touched")
        self.ns["create_payment"]=lambda *a,**k:self.fail("payments must not change")
        with patch.dict(os.environ,{m.STAGING_FLAG:"1","CIKGULAJU_ENVIRONMENT":"staging"},clear=True):
            self.assertTrue(m.install(self.ns,self.path))
        self.assertTrue(self.ns["callback"](5,"mathrph_v45_preview_y6_l117_docx").ok)


if __name__=="__main__":
    unittest.main()
