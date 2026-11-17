from hashlib import sha256
from io import BytesIO
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from zipfile import ZipFile

from web.english_y5_release_preview import BASE, DATA, STAGING_HOST
from web.google_auth_staging_routes import TICKET_COOKIE
from web_google_identity_sessions import issue_google_identity_ticket
from tools.run_google_payments_staging import app


class Year5PreviewTest(TestCase):
    allowed = "00000000-0000-4000-8000-000000000001"
    other = "00000000-0000-4000-8000-000000000002"
    secret = "fixture-signing-secret-" * 3
    origin = "https://" + STAGING_HOST

    def setUp(self):
        staging = "a" * 20
        self.enterContext(patch.dict(os.environ, {
            "CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED": "1",
            "CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED": "1",
            "CIKGULAJU_GOOGLE_RPH_STAGING_TEST_ACCOUNT_ID": self.allowed,
            "CIKGULAJU_GOOGLE_STAGING_PROJECT_REF": staging,
            "CIKGULAJU_GOOGLE_PRODUCTION_PROJECT_REF": "b" * 20,
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_URL": f"https://{staging}.supabase.co",
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_PUBLISHABLE_KEY": "p" * 32,
            "CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY": "s" * 32,
            "CIKGULAJU_GOOGLE_STAGING_ORIGIN": self.origin,
            "CIKGULAJU_GOOGLE_STAGING_ALLOWED_HOST": STAGING_HOST,
            "CIKGULAJU_WEB_SESSION_SECRET": self.secret,
            "CIKGULAJU_AUTHORITATIVE_API_URL": "https://renderer.invalid",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 32,
        }))
        self.profile = self.enterContext(patch(
            "web.google_web_catalog_staging.google_staging_account_profile",
            return_value={"trial_remaining": 9}))
        self.client = app.test_client()

    def get(self, suffix=""):
        return self.client.get(BASE + suffix, base_url=self.origin)

    def sign_in(self, account):
        self.client.set_cookie(TICKET_COOKIE, issue_google_identity_ticket(account, self.secret),
                               domain=STAGING_HOST, secure=True, httponly=True)

    def test_private_allowlisted_downloads_for_both_aliases(self):
        self.assertEqual(self.get().status_code, 303)
        self.assertEqual(self.get().headers["Location"], "/google-staging-login")
        self.assertEqual(self.get("/1.pdf").status_code, 401)
        self.profile.assert_not_called()
        self.sign_in(self.other)
        self.assertEqual(self.get().status_code, 403)
        self.assertEqual(self.get("/1.pdf").status_code, 403)
        self.sign_in(self.allowed)
        self.assertEqual(self.get().status_code, 200)
        metadata = json.loads(DATA.read_text())
        for first, last, tag in ((1, 2, "001-002"), (155, 156, "155-156")):
            for ext in ("docx", "pdf"):
                with self.subTest(tag=tag, format=ext):
                    left, right = self.get(f"/{first}.{ext}"), self.get(f"/{last}.{ext}")
                    self.assertEqual((left.status_code, right.status_code), (200, 200))
                    self.assertEqual(left.data, right.data)
                    self.assertIn(f"_L{tag}.{ext}", left.headers["Content-Disposition"])
                    self.assertEqual(left.headers["X-RPH-Preview-Source-Commit"], metadata["source_commit"])
                    digest = sha256(left.data).hexdigest()
                    self.assertEqual(left.headers["X-RPH-Preview-SHA256"], digest)
                    self.assertEqual(metadata["documents"][tag][ext]["sha256"], digest)
                    self.assertEqual(left.headers["Cache-Control"], "no-store, private")
                    if ext == "pdf":
                        self.assertTrue(left.data.startswith(b"%PDF-"))
                    else:
                        with ZipFile(BytesIO(left.data)) as archive:
                            self.assertIsNone(archive.testzip())
                            self.assertIn(b"5 Amanah", archive.read("word/document.xml"))
        self.assertEqual(self.get("/3.pdf").status_code, 404)
        self.assertEqual(self.get("/1.exe").status_code, 404)

    def test_scope_gate_and_hash_mismatch(self):
        self.sign_in(self.allowed)
        self.assertEqual(self.client.get(BASE, base_url="https://cikgulaju-web.onrender.com").status_code, 404)
        with patch.dict(os.environ, {"CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED": "0"}):
            self.assertEqual(self.get("/1.pdf").status_code, 503)
        with TemporaryDirectory() as folder:
            altered = Path(folder) / "samples.json"
            manifest = json.loads(DATA.read_text())
            manifest["documents"]["001-002"]["pdf"]["sha256"] = "0" * 64
            altered.write_text(json.dumps(manifest))
            with patch("web.english_y5_release_preview.DATA", altered):
                self.assertEqual(self.get("/1.pdf").status_code, 503)
