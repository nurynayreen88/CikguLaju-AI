"""Direct Web RPH -> actual protected Telegram generator contract, no preview UI."""
from io import BytesIO
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from zipfile import ZipFile

from flask import Flask
from web.unified_rph_web import (
    SUBJECT_LABELS, _docx, create_blueprint, source_records, verified_preview
)
from web.telegram_rph_parity import build_layout
from web.native_telegram_rph_client import request_native_rph, NativeRPHUnavailable

ROOT=Path(__file__).resolve().parents[1]


def verified_lesson():
    row=source_records(4,"ENGLISH")[0]
    data=verified_preview(4,"ENGLISH",row["unit"],row["token"])
    assert data
    data["teacher"]={"class":"4 Bestari","date":"2027-03-08","time":"09:15"}
    data["telegram_layout"]=build_layout(data,SUBJECT_LABELS)
    from web.rph_shared_source_identity import source_fingerprint
    data["source_digest"]=source_fingerprint(4,"ENGLISH",row["lesson"])
    assert data["source_digest"]
    return data


class ResponseStub:
    def __init__(self,body,mime):
        self.status=200
        self.headers={"Content-Type":mime}
        self.data=body
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def read(self,n):return self.data[:n]


class OpenerStub:
    def __init__(self,body,mime):
        self.response=ResponseStub(body,mime)
        self.requests=[]
    def open(self,request,timeout):
        self.requests.append((request,timeout))
        return self.response


class NativeWebProxyTests(unittest.TestCase):
    def test_native_word_source_payload_and_token_never_go_to_browser(self):
        data=verified_lesson()
        native_doc=_docx(data).getvalue()
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-ai.onrender.com",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
        }):
            transport=OpenerStub(native_doc,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            payload=request_native_rph(data,"word",opener=transport)
        self.assertEqual(payload.getvalue(),native_doc)
        req,timeout=transport.requests[0]
        self.assertEqual(req.get_method(),"POST")
        self.assertIn("/internal/rph/v1/render",req.full_url)
        self.assertEqual(req.get_header("Authorization"),"Bearer "+"x"*48)
        self.assertLessEqual(timeout,35)
        import json
        body=json.loads(req.data)
        self.assertEqual(body["lesson"],1)
        self.assertEqual(body["subject"],"ENGLISH")
        self.assertIsNone(body["component"])
        self.assertEqual(body["layout"]["style"],"telegram-native-rph-v1")
        self.assertEqual(body["teacher"]["class"],"4 Bestari")
        self.assertEqual(body["source_digest"],data["source_digest"])
        self.assertNotIn("telegram_user_id",body)
        self.assertNotIn("payment",body)
        self.assertNotIn("credits",body)

    def test_pdf_proxy_and_format_errors_fail_closed(self):
        data=verified_lesson()
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-ai.onrender.com",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
        }):
            transport=OpenerStub(b"%PDF-1.4\n"+b"0"*1200,"application/pdf")
            result=request_native_rph(data,"pdf",opener=transport)
            self.assertTrue(result.getvalue().startswith(b"%PDF-"))
            wrong=OpenerStub(b"%PDF-1.4\n"+b"0"*1200,"text/plain")
            with self.assertRaises(NativeRPHUnavailable):
                request_native_rph(data,"pdf",opener=wrong)
            bad=OpenerStub(b"not-a-docx"*200,
                           "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
            with self.assertRaises(NativeRPHUnavailable):
                request_native_rph(data,"word",opener=bad)

    def test_bad_urls_and_missing_token_are_closed(self):
        data=verified_lesson()
        for base in ("http://cikgulaju-ai.onrender.com",
                     "https://user:password@cikgulaju-ai.onrender.com",
                     "https://cikgulaju-ai.onrender.com/evil",
                     "https://cikgulaju-ai.onrender.com:8443"):
            with self.subTest(base=base),patch.dict(os.environ,{
                "CIKGULAJU_AUTHORITATIVE_API_URL":base,
                "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
            }):
                with self.assertRaises(NativeRPHUnavailable):
                    request_native_rph(data,"word",opener=object())

    def test_pjpk_component_identity_is_preserved(self):
        from json import loads
        from web.unified_rph_web import verified_preview
        row=source_records(3,"PJPK","PK")[0]
        data=verified_preview(3,"PJPK",row["unit"],row["token"],"PK")
        data["teacher"]={"class":"","date":"","time":""}
        data["telegram_layout"]=build_layout(data,SUBJECT_LABELS)
        from web.rph_shared_source_identity import source_fingerprint
        data["source_digest"]=source_fingerprint(3,"PJPK",row["lesson"],"PK")
        transport=OpenerStub(_docx(data).getvalue(),
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-ai.onrender.com",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
        }):
            request_native_rph(data,"word",opener=transport)
        request_body=loads(transport.requests[0][0].data)
        self.assertEqual(request_body["component"],"PK")


class WebRouteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client=app.test_client()
        cls.row=source_records(4,"ENGLISH")[0]
        cls.args={"year":4,"subject":"ENGLISH","unit":cls.row["unit"],
                  "lesson":cls.row["token"]}

    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":123},None))
    def test_native_engine_only_both_formats(self,*_):
        with patch("web.native_telegram_rph_client.request_native_rph") as native, \
             patch("web.unified_rph_web._docx",side_effect=AssertionError("old writer must never be used")):
            native.side_effect=lambda selected,fmt: (
                BytesIO(_docx(selected).getvalue()) if fmt=="word" else
                BytesIO(b"%PDF-1.4\n"+b"0"*1200))
            for fmt,endpoint in (("word","/api/web/rph/word"),
                                 ("pdf","/api/web/rph/pdf")):
                with self.subTest(fmt=fmt):
                    result=self.client.get(endpoint,query_string=self.args)
                    self.assertEqual(result.status_code,200,result.get_json() if result.is_json else "")
                    self.assertEqual(result.headers["X-RPH-Generator"],"telegram-native")
                    self.assertEqual(result.headers["Cache-Control"],"no-store, private")
            self.assertEqual(native.call_count,2)
            self.assertEqual(native.call_args.args[1],"pdf")

    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":123},None))
    def test_upstream_failure_does_not_fallback_to_web_generator(self,*_):
        with patch("web.native_telegram_rph_client.request_native_rph",
                   side_effect=NativeRPHUnavailable("unavailable")):
            for endpoint in ("/api/web/rph/word","/api/web/rph/pdf"):
                result=self.client.get(endpoint,query_string=self.args)
                self.assertEqual(result.status_code,503)
                self.assertEqual(result.get_json()["code"],"TELEGRAM_RPH_GENERATOR_UNAVAILABLE")

    @patch("web.unified_rph_web._account",return_value=(None,({"error":"login required"},401)))
    def test_anonymous_forbidden(self,*_):
        self.assertEqual(self.client.get("/api/web/rph/word").status_code,401)
        self.assertEqual(self.client.get("/api/web/rph/pdf").status_code,401)

    def test_no_rph_preview_panel_in_browser_workflow(self):
        html=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        for element in ('id="rph-preview-panel"','id="rph-preview-content"',
                        'id="rph-preview-button"','id="rph-print"'):
            self.assertNotIn(element,html)
        self.assertIn('id="rph-word"',html)
        self.assertIn('id="rph-pdf"',html)
        self.assertIn('generateRphFile("word")',html)
        self.assertIn('generateRphFile("pdf")',html)
        self.assertLess(html.index('id="lesson"'),html.index('id="rph-download-actions"'))


if __name__=="__main__":
    unittest.main()
