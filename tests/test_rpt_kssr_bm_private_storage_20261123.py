"""Offline safety regression for opt-in KSSR BM Word PRIVATE storage.

No network, no teacher data, no billing writes or paid file copies in artifacts.
"""
from __future__ import annotations
from hashlib import sha256
from io import BytesIO
from unittest import TestCase
from unittest.mock import patch
from flask import Flask

from web.rpt_2027_all_http import create_all_rpt_blueprint
from web.rpt_2027_kssr_bm_word import word_document
from web import rpt_kssr_bm_private_storage as private

CONFIG = {
    "account_backend": "supabase",
    "supabase_url": "https://soxakntcanbycjoygrcx.supabase.co",
    "supabase_key": "sb_secret_" + "x" * 48,
}
ENDPOINT = "/api/rpt/2027/all/bahasa_melayu/2.docx"
FLAG = "CIKGULAJU_KSSR_BM_WORD_PRIVATE"


class MockResponse:
    status = 200
    def __init__(self, payload):
        self.payload = payload
    def __enter__(self):
        return self
    def __exit__(self, *_args):
        return False
    def read(self, limit):
        return self.payload[:limit]


class PrivateStorageTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = Flask(__name__)
        cls.app.register_blueprint(create_all_rpt_blueprint())
        cls.client = cls.app.test_client()
        cls.source = word_document(2)[0].read_bytes()

    def test_manifest_is_verified_without_local_docx(self):
        for year in range(2, 7):
            self.assertIsNotNone(private.verified_manifest_entry(year))
        self.assertIsNone(private.verified_manifest_entry(1))
        self.assertIsNone(private.verified_manifest_entry(7))

    def test_direct_private_reader_checks_hash_and_fixed_path(self):
        captured = []
        def opener(req, timeout):
            captured.append((req, timeout))
            return MockResponse(self.source)
        blob, digest = private.fetch_document(2, CONFIG, opener=opener)
        self.assertEqual(blob, self.source)
        self.assertEqual(digest, sha256(self.source).hexdigest())
        request, timeout = captured[0]
        self.assertEqual(timeout, 12)
        self.assertEqual(request.full_url, "https://soxakntcanbycjoygrcx.supabase.co/storage/v1/object/authenticated/cikgulaju-materials/rpt-premium/bahasa-melayu-kssr-2027/tahun_2.docx")
        self.assertEqual(request.get_header("Apikey"), CONFIG["supabase_key"])
        self.assertNotIn("Authorization", request.headers)

    def test_modified_or_oversized_binary_fails_closed(self):
        for data in [self.source + b"x", b"fake_docx", self.source[:-1]]:
            with self.subTest(size=len(data)), self.assertRaises(private.PrivateWordUnavailable):
                private.fetch_document(2, CONFIG, opener=lambda *_a, **_k: MockResponse(data))

    def test_publishable_key_and_redirect_are_rejected(self):
        config = dict(CONFIG, supabase_key="sb_publishable_"+"x"*45)
        with self.assertRaises(private.PrivateWordUnavailable):
            private.fetch_document(2, config, opener=lambda *_a, **_k: MockResponse(self.source))
        from urllib.error import HTTPError
        with self.assertRaises(private.PrivateWordUnavailable):
            private.fetch_document(2, CONFIG, opener=lambda *_a, **_k: (_ for _ in ()).throw(HTTPError("https://redirect.invalid",302,"redirect",{},None)))

    def test_paid_private_endpoint_returns_bytes_as_attachment_not_url(self):
        account={"telegram_user_id":23,"authenticated":True,"rakan_pembangun":True}
        with patch.dict("os.environ",{FLAG:"1"}), \
             patch("web.rpt_2027_all_http._account",return_value=(account,None)), \
             patch("web.rpt_2027_all_http._has_paid_access",return_value=True), \
             patch("web_v1_telegram_auth_routes._config",return_value=CONFIG), \
             patch("web.rpt_kssr_bm_private_storage.fetch_document",return_value=(self.source,sha256(self.source).hexdigest())) as fetch:
            resp=self.client.get(ENDPOINT)
            self.assertEqual(resp.status_code,200)
            self.assertEqual(resp.data,self.source)
            self.assertIn("attachment",resp.headers["Content-Disposition"])
            self.assertEqual(resp.headers["Cache-Control"],"no-store, private")
            self.assertNotIn("soxaknt",resp.headers["Content-Disposition"])
            fetch.assert_called_once()

    def test_free_user_cannot_trigger_private_read(self):
        account={"telegram_user_id":22,"authenticated":True,"free_generations_remaining":10}
        with patch.dict("os.environ",{FLAG:"1"}), \
             patch("web.rpt_2027_all_http._account",return_value=(account,None)), \
             patch("web.rpt_2027_all_http._has_paid_access",return_value=False), \
             patch("web.rpt_kssr_bm_private_storage.fetch_document") as fetch:
            resp=self.client.get(ENDPOINT)
            self.assertEqual(resp.status_code,403)
            fetch.assert_not_called()

    def test_private_read_failure_does_not_fall_back_to_public_git_file(self):
        account={"telegram_user_id":23,"authenticated":True,"rakan_pembangun":True}
        with patch.dict("os.environ",{FLAG:"1"}), \
             patch("web.rpt_2027_all_http._account",return_value=(account,None)), \
             patch("web.rpt_2027_all_http._has_paid_access",return_value=True), \
             patch("web_v1_telegram_auth_routes._config",return_value=CONFIG), \
             patch("web.rpt_kssr_bm_private_storage.fetch_document",side_effect=private.PrivateWordUnavailable):
            resp=self.client.get(ENDPOINT)
            self.assertEqual(resp.status_code,503)

    def test_unset_flag_preserves_existing_paid_download(self):
        account={"telegram_user_id":23,"authenticated":True,"rakan_pembangun":True}
        with patch.dict("os.environ",{FLAG:"0"}), \
             patch("web.rpt_2027_all_http._account",return_value=(account,None)), \
             patch("web.rpt_2027_all_http._has_paid_access",return_value=True), \
             patch("web.rpt_kssr_bm_private_storage.fetch_document") as fetch:
            resp=self.client.get(ENDPOINT)
            self.assertEqual(resp.status_code,200)
            self.assertEqual(resp.data,self.source)
            fetch.assert_not_called()
