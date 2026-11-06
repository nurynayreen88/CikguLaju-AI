"""Web Sejarah only trusts authenticated, matching Telegram source."""
import io
import unittest
from unittest.mock import patch

from flask import Flask

from web.native_telegram_rph_client import NativeRPHUnavailable, MIMES
from web.native_telegram_sejarah_2027_client import (
    list_sejarah_units, list_sejarah_lessons, sejarah_available,
    request_sejarah_rph,
)


class Response:
    status = 200
    def __init__(self, data, mime="application/pdf"):
        self.data = data
        self.headers = {"Content-Type": mime}
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False
    def read(self, n):
        return self.data[:n]


class Opener:
    def __init__(self, response):
        self.response = response
        self.last = None
    def open(self, req, timeout):
        self.last = req
        return self.response


class SejarahClientTest(unittest.TestCase):
    def test_valid_and_invalid_source_catalog(self):
        with patch("web.native_telegram_sejarah_2027_client._read",
                   return_value={"source":"telegram-sejarah-2027-v1",
                                 "items":[{"value":"u01","label":"Unit 1: Sejarah"}]}):
            self.assertEqual(list_sejarah_units(4)[0]["value"], "u01")
        with patch("web.native_telegram_sejarah_2027_client._read",
                   return_value={"source":"different-source",
                                 "items":[{"value":"u01","label":"Unit 1: Sejarah"}]}):
            with self.assertRaises(NativeRPHUnavailable):
                list_sejarah_units(4)
        with self.assertRaises(ValueError):
            list_sejarah_units(3)
        with self.assertRaises(ValueError):
            list_sejarah_lessons(5,"u00")

    def test_pdp_sources_preserve_printed_page_references(self):
        record = {"value":"007","label":"PdP 007 — Agama Islam",
                  "textbook_ref":"Buku Teks m/s 25"}
        with patch("web.native_telegram_sejarah_2027_client._read",
                   return_value={"source":"telegram-sejarah-2027-v1",
                                 "items":[record]}):
            self.assertEqual(list_sejarah_lessons(5, "u02"), [record])
        with patch("web.native_telegram_sejarah_2027_client._read",
                   return_value={"source":"telegram-sejarah-2027-v1",
                                 "items":[{"value":"007","label":"PdP 007"}]}):
            with self.assertRaises(NativeRPHUnavailable):
                list_sejarah_lessons(5, "u02")

    def test_readiness_is_strict(self):
        with patch("web.native_telegram_sejarah_2027_client._read",
                   return_value={"available":True}):
            self.assertTrue(sejarah_available(5,"u02","007"))
        with patch("web.native_telegram_sejarah_2027_client._read",
                   return_value={"available":False}):
            with self.assertRaises(NativeRPHUnavailable):
                sejarah_available(5,"u02","007")

    def test_word_pdf_only_from_trusted_native_endpoint(self):
        payload={"source":"telegram-native-sejarah-2027",
                 "year":5,"unit":"u02","lesson":"007",
                 "teacher":{"class":"5 Bestari","date":"2027-03-22",
                            "time":"08:00-09:00","students":""}}
        with patch("web.native_telegram_sejarah_2027_client._backend",
                   return_value=("https://example.org","X"*48)):
            pdf = Opener(Response(b"%PDF-1.5\n" + b"A"*1800))
            self.assertTrue(request_sejarah_rph(payload,"pdf",opener=pdf).getvalue().startswith(b"%PDF"))
            self.assertEqual(pdf.last.get_method(), "POST")
            self.assertIn("/internal/rph/v1/sejarah/render", pdf.last.full_url)
            with self.assertRaises(NativeRPHUnavailable):
                request_sejarah_rph(payload,"word",
                    opener=Opener(Response(b"%PDF-1.5\n" + b"A"*1800,
                        mime=MIMES["word"])))
        with self.assertRaises(ValueError):
            request_sejarah_rph({**payload,"lesson":"../../007"},"pdf")
        with self.assertRaises(ValueError):
            request_sejarah_rph({**payload,"source":"unverified-copy"},"pdf")

    def test_unified_web_uses_existing_access_and_quota_gate(self):
        from web.unified_rph_web import create_blueprint
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        with app.test_client() as client:
            url="/api/web/rph/availability?year=5&subject=SEJARAH&unit=u02&lesson=007"
            account={"telegram_user_id":123,"free_remaining":10}
            with patch("web.unified_rph_web._account",return_value=(account,None)), \
                 patch("web.unified_rph_web._has_paid_access",return_value=True), \
                 patch("web.native_telegram_sejarah_2027_client.sejarah_available",
                       return_value=True):
                response=client.get(url)
                self.assertEqual(response.status_code,200)
                self.assertTrue(response.json["available"])
                preview=client.get(url.replace("/availability","/preview"))
                self.assertEqual(preview.status_code,200)
                self.assertEqual(preview.json["source"],"telegram-native-sejarah-2027")
                self.assertEqual(preview.json["status"],"DRAF CADANGAN")
            with patch("web.unified_rph_web._account",return_value=(account,None)), \
                 patch("web.unified_rph_web._has_paid_access",return_value=False):
                response=client.get(url.replace("lesson=007","lesson=008"))
                self.assertNotEqual(response.status_code,200)


if __name__ == "__main__":
    unittest.main()
