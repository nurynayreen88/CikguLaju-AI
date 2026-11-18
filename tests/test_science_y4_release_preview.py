from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
from zipfile import ZipFile

from tools.run_google_payments_staging import app
from web.english_y5_release_preview import STAGING_HOST
from web.google_auth_staging_routes import TICKET_COOKIE
from web.science_y4_release_preview import BASE, DATA, LESSONS, SOURCE_COMMIT
from web_google_identity_sessions import issue_google_identity_ticket


class ScienceYear4StagingTest(TestCase):
    allowed = "00000000-0000-4000-8000-000000000001"
    other = "00000000-0000-4000-8000-000000000002"
    secret = "fixture-signing-secret-" * 3
    origin = "https://" + STAGING_HOST

    def setUp(self):
        staging = "a" * 20
        self.enterContext(patch.dict("os.environ", {
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

    def sign_in(self, account):
        ticket = issue_google_identity_ticket(account, self.secret)
        self.client.set_cookie(TICKET_COOKIE, ticket, domain=STAGING_HOST, secure=True, httponly=True)

    def get(self, suffix=""):
        return self.client.get(BASE + suffix, base_url=self.origin)

    def test_only_the_staging_teacher_can_download_the_approved_files(self):
        anonymous = self.get()
        self.assertEqual(anonymous.status_code, 303)
        self.assertEqual(anonymous.headers["Location"], "/google-staging-login")
        self.assertEqual(self.get("/lesson-46.pdf").status_code, 401)
        self.profile.assert_not_called()
        self.sign_in(self.other)
        self.assertEqual(self.get().status_code, 403)
        self.assertEqual(self.get("/lesson-46.docx").status_code, 403)
        self.sign_in(self.allowed)
        page = self.get()
        self.assertEqual(page.status_code, 200)
        self.assertIn(SOURCE_COMMIT[:7].encode(), page.data)
        metadata = json.loads(DATA.read_text())
        for lesson, (lesson_id, label) in LESSONS.items():
            for extension in ("docx", "pdf"):
                with self.subTest(lesson=lesson, extension=extension):
                    path = f"/{lesson}.{extension}"
                    self.assertIn(path.encode(), page.data)
                    response = self.get(path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(f"{lesson_id}.{extension}", response.headers["Content-Disposition"])
                    self.assertEqual(response.headers["Cache-Control"], "no-store, private")
                    digest = sha256(response.data).hexdigest()
                    self.assertEqual(digest, response.headers["X-RPH-Preview-SHA256"])
                    self.assertEqual(digest, metadata["documents"][lesson][extension]["sha256"])
                    self.assertEqual(response.headers["X-RPH-Preview-Source-Commit"], SOURCE_COMMIT)
                    if extension == "pdf":
                        self.assertTrue(response.data.startswith(b"%PDF-"))
                    else:
                        with ZipFile(BytesIO(response.data)) as document:
                            self.assertIsNone(document.testzip())
                            self.assertIn(label.split(" · ")[1].encode(), document.read("word/document.xml"))
        self.assertEqual(self.get("/lesson-47.pdf").status_code, 404)

    def test_rejects_a_different_host_or_version(self):
        self.sign_in(self.allowed)
        self.assertEqual(self.client.get(BASE, base_url="https://cikgulaju-web.onrender.com").status_code, 404)
        with TemporaryDirectory() as folder:
            altered = Path(folder) / "samples.json"
            manifest = json.loads(DATA.read_text())
            manifest["source_commit"] = "0" * 40
            altered.write_text(json.dumps(manifest))
            with patch("web.science_y4_release_preview.DATA", altered):
                self.assertEqual(self.get("/lesson-46.pdf").status_code, 503)
