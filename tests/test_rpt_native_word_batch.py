import unittest
from unittest.mock import patch
from pathlib import Path
from hashlib import sha256
from tempfile import TemporaryDirectory
from web import rpt_native_word_batch as batch
from web.rpt_2027_all_http import create_all_rpt_blueprint
from flask import Flask

class PrivateBatchTests(unittest.TestCase):
    def test_scope_and_default_off(self):
        self.assertEqual(len(batch.PINS),31)
        self.assertFalse(any(k.startswith(("bahasa_melayu:","english:","bahasa_arab:","pendidikan_islam:")) for k in batch.PINS))
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"0"}):
            self.assertFalse(batch.enabled())
    def test_source_digest_gate(self):
        with TemporaryDirectory() as folder, patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}):
            root=Path(folder)
            source=root/"web_2027_pdfs"/"muzik"/"tahun_2.pdf"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"%PDF-"+b"x"*8000)
            with patch.dict(batch.PINS,{"muzik:2":sha256(source.read_bytes()).hexdigest()}):
                self.assertTrue(batch.eligible("muzik",2,source,root=root))
                source.write_bytes(b"%PDF-"+b"y"*8000)
                self.assertFalse(batch.eligible("muzik",2,source,root=root))
    def test_entitlement_before_generation(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"free_generations_remaining":10},None)), patch("web.rpt_2027_all_http.native_word.document") as generate:
            response=app.test_client().get("/api/rpt/2027/all/muzik/2.docx")
            self.assertEqual(response.status_code,403)
            generate.assert_not_called()
    def test_paid_attachment(self):
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web.rpt_2027_all_http._account",return_value=({"telegram_user_id":9,"rakan_pembangun":True},None)), patch("web.rpt_2027_all_http._staged_file",return_value=Path("example.pdf")), patch("web_v1_telegram_auth_routes._config",return_value={}), patch("web.rpt_2027_all_http.native_word.document",return_value=(b"mock-docx","digest")):
            response=app.test_client().get("/api/rpt/2027/all/muzik/2.docx")
            self.assertEqual(response.status_code,200)
            self.assertEqual(response.data,b"mock-docx")
            self.assertIn("attachment",response.headers["Content-Disposition"])
            self.assertEqual(response.headers["Cache-Control"],"no-store, private")
    def test_actual_paid_word_and_unchanged_pdf_for_each_subject(self):
        import io
        from docx import Document
        from PIL import Image
        from web.rpt_2027_all_http import ROOT, catalog_data
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        crest=io.BytesIO();Image.new("RGB",(48,48),"#28553a").save(crest,format="PNG")
        identity={"school":"SEKOLAH KEBANGSAAN CONTOH","teacher":"GURU CONTOH","state":"","logo":crest.getvalue()}
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        cases={}
        for key in batch.PINS:
            subject,year=key.split(":")
            cases.setdefault(subject,int(year))
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}), patch("web.rpt_school_cover.school_identity",return_value=identity) as profile:
            for subject,year in cases.items():
                with self.subTest(subject=subject,year=year):
                    url=f"/api/rpt/2027/all/{subject}/{year}"
                    with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                        pdf=client.get(url+".pdf")
                        self.assertEqual(pdf.status_code,200)
                        self.assertEqual(sha256(pdf.data).hexdigest(),batch.PINS[f"{subject}:{year}"])
                        word=client.get(url+".docx")
                        self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else "")
                        self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                        self.assertIn("attachment",word.headers["Content-Disposition"])
                        document=Document(io.BytesIO(word.data))
                        self.assertEqual(len(document.tables),1)
                        self.assertGreater(len(document.tables[0].rows),1)
                        self.assertTrue(document.paragraphs[0]._p.xpath(".//wp:anchor"))
                    before=profile.call_count
                    with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                        self.assertEqual(client.get(url+".docx").status_code,403)
                        self.assertEqual(client.get(url+".pdf").data,pdf.data)
                    self.assertEqual(profile.call_count,before)
            paid_catalog=catalog_data(root=ROOT,personalization_allowed=True)
            free_catalog=catalog_data(root=ROOT,personalization_allowed=False)
            def advertised(data):
                return {f"{subject['code']}:{year['year']}" for subject in data["subjects"] for year in subject["years"] if year.get("docx_ready")}
            self.assertTrue(set(batch.PINS).issubset(advertised(paid_catalog)))
            self.assertFalse(set(batch.PINS)&advertised(free_catalog))


    def test_approved_science_word_paid_only_and_exact_source(self):
        import io
        from docx import Document
        from web.rpt_2027_all_http import ROOT, catalog_data
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}), patch("web.rpt_school_cover.school_identity",return_value=None) as profile:
            for year,source_digest in batch.APPROVED_SCIENCE_PINS.items():
                url=f"/api/rpt/2027/all/sains/{year}"
                with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                    pdf=client.get(url+".pdf")
                    self.assertEqual(pdf.status_code,200)
                    self.assertEqual(sha256(pdf.data).hexdigest(),source_digest)
                    word=client.get(url+".docx")
                    self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else "")
                    doc=Document(io.BytesIO(word.data))
                    self.assertGreater(len(doc.tables),1)
                    self.assertGreater(len(doc.tables[0].rows),1)
                    self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                before=profile.call_count
                with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                    self.assertEqual(client.get(url+".docx").status_code,403)
                    self.assertEqual(client.get(url+".pdf").data,pdf.data)
                self.assertEqual(profile.call_count,before)
            for access in (True,False):
                subjects=catalog_data(root=ROOT,personalization_allowed=access)["subjects"]
                science=next(x for x in subjects if x["code"]=="sains")
                for y in science["years"]:
                    if y["year"] in batch.APPROVED_SCIENCE_PINS:
                        self.assertEqual(y.get("docx_ready"),access)


    def test_approved_math_word_paid_only_and_exact_source(self):
        import io
        from docx import Document
        from rpt_2027.matematik import sk_documents
        from web.rpt_2027_all_http import ROOT, catalog_data
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}), patch("web.rpt_school_cover.school_identity",return_value=None) as profile:
            for year,source_digest in sk_documents.DIGESTS.items():
                url=f"/api/rpt/2027/all/matematik/{year}"
                with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                    pdf=client.get(url+".pdf")
                    self.assertEqual(pdf.status_code,200)
                    self.assertEqual(sha256(pdf.data).hexdigest(),source_digest)
                    word=client.get(url+".docx")
                    self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else "")
                    doc=Document(io.BytesIO(word.data))
                    self.assertGreater(len(doc.tables),1)
                    self.assertGreater(sum(len(t.rows)-1 for t in doc.tables),116)
                    self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                before=profile.call_count
                with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                    self.assertEqual(client.get(url+".docx").status_code,403)
                    self.assertEqual(client.get(url+".pdf").data,pdf.data)
                self.assertEqual(profile.call_count,before)
            for access in (True,False):
                subjects=catalog_data(root=ROOT,personalization_allowed=access)["subjects"]
                math=next(x for x in subjects if x["code"]=="matematik")
                for y in math["years"]:
                    if y["year"] in sk_documents.DIGESTS:
                        self.assertEqual(y.get("docx_ready"),access)


    def test_integrated_english_paid_word(self):
        import io
        import json
        from docx import Document
        from web.rpt_2027_all_http import ROOT, catalog_data
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint())
        client=app.test_client()
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        lock=json.loads((ROOT/"web_2027_pdfs"/"original_cover_layout_verified.json").read_text())
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}), patch("web.native_telegram_integrated_english_client.integrated_enabled",return_value=True), patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}), patch("web.rpt_school_cover.school_identity",return_value=None):
            for year in range(2,7):
                url=f"/api/rpt/2027/all/english/{year}"
                with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                    pdf=client.get(url+".pdf")
                    self.assertEqual(pdf.status_code,200)
                    self.assertEqual(sha256(pdf.data).hexdigest(),lock["english_integrated"]["source_sha256_by_subject_year"][f"english:{year}"])
                    word=client.get(url+".docx")
                    self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else "")
                    self.assertGreaterEqual(sum(len(t.rows)-1 for t in Document(io.BytesIO(word.data)).tables),160)
                    self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                    self.assertEqual(client.get(url+".docx").status_code,403)
                    self.assertEqual(client.get(url+".pdf").data,pdf.data)


    def test_dlp_paid_word_all_ten(self):
        import io
        from docx import Document
        from web.rpt_2027_all_http import ROOT,catalog_data
        from tools.build_rpt_dlp_native_20261126 import PINS
        app=Flask(__name__);app.register_blueprint(create_all_rpt_blueprint());client=app.test_client()
        paid={"telegram_user_id":9,"rakan_pembangun":True}
        free={"telegram_user_id":10,"free_generations_remaining":10}
        with patch.dict("os.environ",{"CIKGULAJU_RPT_NATIVE_WORD_BATCH":"1"}),patch("web_v1_telegram_auth_routes._config",return_value={"account_backend":"supabase"}),patch("web.rpt_school_cover.school_identity",return_value=None) as profile:
            for key,digest in PINS.items():
                subject,y=key.split(":")
                url=f"/api/rpt/2027/all/{subject}/{y}"
                with patch("web.rpt_2027_all_http._account",return_value=(paid,None)):
                    pdf=client.get(url+".pdf")
                    self.assertEqual(pdf.status_code,200,key)
                    self.assertEqual(sha256(pdf.data).hexdigest(),digest)
                    word=client.get(url+".docx")
                    self.assertEqual(word.status_code,200,word.get_data(as_text=True) if word.status_code!=200 else "")
                    self.assertGreater(len(Document(io.BytesIO(word.data)).tables[0].rows),50)
                    self.assertEqual(word.headers["Cache-Control"],"no-store, private")
                calls=profile.call_count
                with patch("web.rpt_2027_all_http._account",return_value=(free,None)):
                    self.assertEqual(client.get(url+".docx").status_code,403)
                    self.assertEqual(client.get(url+".pdf").data,pdf.data)
                self.assertEqual(profile.call_count,calls)
            for access in (False,True):
                subjects=catalog_data(root=ROOT,personalization_allowed=access)["subjects"]
                for code in ("mathematics_dlp","science_dlp"):
                    rows=next(x for x in subjects if x["code"]==code)["years"]
                    self.assertEqual(len(rows),5)
                    self.assertTrue(all(y["docx_ready"]==access for y in rows))

if __name__=="__main__": unittest.main()
