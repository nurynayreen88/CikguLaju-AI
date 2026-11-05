"""Web RPH metadata: strict class, PdP start/end and pupil counts.

The resulting teacher data must reach the same Telegram-native RPH layout.
No writes to user profiles or curriculum databases are needed.
"""
import unittest
from unittest.mock import patch
from flask import Flask
from web.unified_rph_web import create_blueprint, source_records
import json
import os
from web.unified_rph_web import _docx
from web.native_telegram_rph_client import request_native_rph


class RphMetadataTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client=app.test_client()
        row=source_records(4,"ENGLISH")[0]
        cls.query={"year":"4","subject":"ENGLISH","unit":row["unit"],"lesson":row["token"]}
        cls.auth=patch("web.unified_rph_web._account",
                       return_value=({"telegram_user_id":123},None))
        cls.paid=patch("web.unified_rph_web._has_paid_access",return_value=True)
        cls.auth.start();cls.paid.start()

    @classmethod
    def tearDownClass(cls):
        cls.paid.stop();cls.auth.stop()

    def preview(self,**fields):
        return self.client.get("/api/web/rph/preview",query_string={**self.query,**fields})

    def test_all_fields_reach_telegram_header_and_native_generator_state(self):
        response=self.preview(
            teacher_class="4 Bestari",teacher_date="2027-03-08",
            teacher_start="07:30",teacher_end="08:30",teacher_students="32")
        self.assertEqual(response.status_code,200,response.get_json() if response.is_json else "")
        document=response.get_json()
        self.assertEqual(document["teacher"],{
            "class":"4 Bestari","date":"2027-03-08",
            "time":"07:30 - 08:30","students":"32"})
        header={item["label"]:item["value"] for item in document["telegram_layout"]["header"]}
        self.assertEqual(header["Class"],"4 Bestari")
        self.assertEqual(header["Time"],"07:30 - 08:30")
        self.assertEqual(header["Number of Pupils"],"32")
        # Verify the actual private HTTPS payload that the Web sends to the
        # Telegram generator; no second Web RPH renderer is substituted.
        native_doc=_docx(document).getvalue()
        class NativeReply:
            status=200
            headers={"Content-Type":"application/vnd.openxmlformats-officedocument.wordprocessingml.document"}
            def __enter__(self):return self
            def __exit__(self,*a):return False
            def read(self,n):return native_doc[:n]
        class NativeTransport:
            def __init__(self):self.req=None
            def open(self,req,timeout):self.req=req;return NativeReply()
        transport=NativeTransport()
        with patch.dict(os.environ,{
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-ai.onrender.com",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*48,
        }):
            request_native_rph(document,"word",opener=transport)
        sent=json.loads(transport.req.data)
        self.assertEqual(sent["format"],"word")
        self.assertEqual(sent["teacher"]["class"],"4 Bestari")
        self.assertEqual(sent["teacher"]["time"],"07:30 - 08:30")
        self.assertEqual(sent["teacher"]["students"],"32")
        native_header={i["label"]:i["value"] for i in sent["layout"]["header"]}
        self.assertEqual(native_header["Number of Pupils"],"32")

    def test_optional_fields_and_old_time_format_stay_compatible(self):
        response=self.preview()
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.get_json()["teacher"]["students"],"")
        self.assertEqual(response.get_json()["teacher"]["time"],"")
        old=self.preview(teacher_time="09:15")
        self.assertEqual(old.status_code,200)
        self.assertEqual(old.get_json()["teacher"]["time"],"09:15")
        old_range=self.preview(teacher_time="09:15 - 10:15")
        self.assertEqual(old_range.status_code,200)
        self.assertEqual(old_range.get_json()["teacher"]["time"],"09:15 - 10:15")

    def test_incomplete_invalid_or_inverted_time_rejected(self):
        for extra in (
            {"teacher_start":"07:30"},
            {"teacher_end":"08:30"},
            {"teacher_start":"08:30","teacher_end":"07:30"},
            {"teacher_start":"08:30","teacher_end":"08:30"},
            {"teacher_start":"25:00","teacher_end":"26:00"},
            {"teacher_start":"07:30","teacher_end":"08:30","teacher_time":"09:00"},
            {"teacher_time":"26:00"},
        ):
            with self.subTest(extra=extra):
                r=self.preview(**extra)
                self.assertEqual(r.status_code,400,r.get_json())

    def test_invalid_pupil_count_rejected(self):
        for num in ("0","201","-5","1.5","1e2","023","999","9999","abc"):
            with self.subTest(num=num):
                r=self.preview(teacher_students=num)
                self.assertEqual(r.status_code,400,r.get_json())
        self.assertEqual(self.preview(teacher_students="1").status_code,200)
        self.assertEqual(self.preview(teacher_students="200").status_code,200)

    def test_malformed_or_duplicate_keys_are_not_accepted(self):
        r=self.client.get("/api/web/rph/preview",
                          query_string=list(self.query.items())+
                          [("teacher_students","32"),("teacher_students","33")])
        self.assertEqual(r.status_code,400)
        self.assertEqual(self.preview(teacher_class="<script>").status_code,400)
        self.assertEqual(self.preview(malicious_key="hack").status_code,400)


if __name__=="__main__":
    unittest.main()
