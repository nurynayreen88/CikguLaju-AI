"""Browser route integration with in-memory private staging backend.

Mock only external network/native generator. Exercise the real Flask HTTP
issue -> generate -> download endpoints together. No Supabase or production
writes; SQL-ledger/storage internals have separate PostgreSQL integration CI.
"""
from io import BytesIO
from zipfile import ZipFile, ZIP_STORED
from unittest.mock import patch
import unittest

from flask import Flask

from web.google_rph_generation_staging_routes import bp as generation_bp
from web.google_rph_bundle_delivery import bp as delivery_bp
from web.google_native_rph_bundle import NativeGoogleRPHNotReady
from web.google_rph_bundle_quota import rendered_bundle_sha256
from web.provider_neutral_web_identity import from_verified_google_account


OWNER = "1a267083-8511-4587-a585-857fe35f4a14"
OTHER = "c1351d2d-591d-4ae4-8c92-b0e14d2c3234"
CFG = {"secret": "google-integration-only-" + "x" * 45,
       "origin": "https://cikgulaju-google-payments-staging.onrender.com",
       "supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co",
       "staging_service_key": "sb_secret_" + "x" * 42}
SELECTION = {"year": 3, "subject": "ENGLISH", "component": None,
             "unit": "Unit One", "lesson": "e-3-003"}
TEACHER = {"class": "3 Amanah", "date": "2026-11-07",
           "time": "08:00 - 09:00", "students": "28"}
REQUEST = {"selection": SELECTION, "teacher": TEACHER}


def word_bytes():
    buffer = BytesIO()
    with ZipFile(buffer, "w", ZIP_STORED) as archive:
        archive.writestr("[Content_Types].xml", "<Types/>" * 30)
        archive.writestr("word/document.xml", "<document>" + "x" * 650 + "</document>")
    return buffer.getvalue()


WORD = word_bytes()
PDF = b"%PDF-1.7\n" + b"x" * 650 + b"\n%%EOF\n"
MANIFEST = rendered_bundle_sha256(WORD, PDF)


class GoogleRPHHTTPFlowTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(generation_bp)
        app.register_blueprint(delivery_bp)
        self.client = app.test_client()
        self.current = OWNER
        self.credits = 10
        self.jobs = {}
        self.files = {}
        self.debits = 0
        self.native_calls = 0
        self.patches = [
            patch("web.google_rph_generation_staging_routes._generator_config",
                  return_value=CFG),
            patch("web.google_rph_generation_staging_routes._staging_test_account",
                  return_value=OWNER),
            patch("web.google_rph_generation_staging_routes._actor", new=self.actor),
            patch("web.google_rph_bundle_delivery._actor", new=self.actor),
            patch("web.google_rph_bundle_delivery._enabled_config", return_value=CFG),
            patch("web.google_rph_generation_staging_routes.google_staging_account_profile",
                  new=self.profile),
            patch("web.unified_rph_web.pdp_options",
                  return_value=[{"value": SELECTION["lesson"]}]),
            patch("web.google_rph_generation_staging_routes.prepare_private_bundle",
                  new=self.prepare),
            patch("web.google_rph_generation_staging_routes._ready_job",
                  new=self.ready_job),
            patch("web.google_rph_bundle_delivery._ready_job", new=self.ready_job),
            patch("web.google_rph_generation_staging_routes.render_native_google_rph_bundle",
                  new=self.render),
            patch("web.google_rph_generation_staging_routes.publish_rendered_bundle",
                  new=self.publish),
            patch("web.google_rph_bundle_delivery._private_file",
                  new=self.private_file),
        ]
        for handle in self.patches:
            handle.start()
            self.addCleanup(handle.stop)

    def actor(self):
        return from_verified_google_account(
            self.current, {"account_id": self.current,
                           "trial_remaining": self.credits}), None

    def profile(self, cfg, account_id):
        self.assertEqual(cfg, CFG)
        self.assertEqual(account_id, self.current)
        return {"trial_remaining": self.credits}

    def prepare(self, cfg, actor, job, digest):
        self.assertEqual(actor.account_id, self.current)
        previous = self.jobs.get(job)
        if previous is None:
            self.jobs[job] = {
                "id": job, "account_id": actor.account_id,
                "selection_hash": digest, "status": "prepared"}
        else:
            self.assertEqual(previous["selection_hash"], digest)
            self.assertEqual(previous["account_id"], actor.account_id)
        return {"job_id": job, "status": self.jobs[job]["status"]}

    def ready_job(self, cfg, actor, job):
        row = self.jobs.get(job)
        return row if row and row["account_id"] == actor.account_id else None

    def render(self, year, subject, unit, lesson, teacher, component=None):
        self.assertEqual((year, subject, unit, lesson, component),
                         (3, "ENGLISH", "Unit One", "e-3-003", None))
        self.assertEqual(teacher, TEACHER)
        self.native_calls += 1
        return {"word": WORD, "pdf": PDF}

    def publish(self, cfg, actor, job, digest, word, pdf):
        self.assertEqual(actor.account_id, self.current)
        self.assertEqual(self.jobs[job]["selection_hash"], digest)
        self.assertEqual(rendered_bundle_sha256(word, pdf), MANIFEST)
        row = self.jobs[job]
        if row["status"] == "ready":
            return {"job_id": job, "status": "ready",
                    "already_ready": True, "allowed": True,
                    "remaining": self.credits}
        if self.credits == 0:
            return {"job_id": job, "status": "prepared", "allowed": False,
                    "remaining": 0}
        self.credits -= 1
        self.debits += 1
        row.update({"status": "ready", "document_manifest_sha256": MANIFEST})
        self.files[(actor.account_id, job, "word")] = word
        self.files[(actor.account_id, job, "pdf")] = pdf
        return {"job_id": job, "status": "ready",
                "allowed": True, "remaining": self.credits}

    def private_file(self, cfg, account, job, fmt):
        self.assertEqual(account, self.current)
        return self.files[(account, job, fmt)]

    def post(self, path, body, *, origin=CFG["origin"]):
        return self.client.post(path, json=body,
                                headers={"Origin": origin,
                                         "Sec-Fetch-Site": "same-origin"})

    def issue(self):
        result = self.post("/api/google-staging/web/rph/issue", REQUEST)
        self.assertEqual(result.status_code, 200, result.json)
        self.assertFalse(result.json["charged"])
        return result.json

    def generate(self, ticket):
        return self.post("/api/google-staging/web/rph/generate",
                         {**REQUEST, "ticket": ticket})

    def test_full_native_word_pdf_ready_retry_and_owner_isolation(self):
        issued = self.issue()
        job_id = issued["job_id"]
        first = self.generate(issued["ticket"])
        self.assertEqual(first.status_code, 200, first.json)
        self.assertEqual(first.json["remaining"], 9)
        self.assertEqual(self.debits, 1)
        self.assertEqual(self.native_calls, 1)
        self.assertEqual(self.jobs[job_id]["status"], "ready")
        repeated = self.generate(issued["ticket"])
        self.assertEqual(repeated.status_code, 200, repeated.json)
        self.assertTrue(repeated.json["already_ready"])
        self.assertEqual(self.debits, 1)
        self.assertEqual(self.native_calls, 1)

        for fmt, expected in (("word", WORD), ("pdf", PDF)):
            download = self.client.get(
                f"/api/google-staging/web/rph/jobs/{job_id}/download/{fmt}")
            self.assertEqual(download.status_code, 200)
            self.assertEqual(download.data, expected)
            self.assertEqual(download.headers["X-RPH-Generator"], "telegram-native")
        self.assertEqual(self.credits, 9)
        self.current = OTHER
        self.assertEqual(self.generate(issued["ticket"]).status_code, 403)
        self.assertEqual(self.client.get(
            f"/api/google-staging/web/rph/jobs/{job_id}/download/pdf").status_code, 404)
        self.assertEqual(self.debits, 1)

    def test_native_failure_never_charges_or_releases_prepared_file(self):
        issued = self.issue()
        self.assertEqual(self.credits, 10)
        job_id = issued["job_id"]
        with patch("web.google_rph_generation_staging_routes.render_native_google_rph_bundle",
                   side_effect=NativeGoogleRPHNotReady("offline")):
            failed = self.generate(issued["ticket"])
        self.assertEqual(failed.status_code, 503)
        self.assertEqual(self.credits, 10)
        self.assertEqual(self.debits, 0)
        self.assertEqual(self.client.get(
            f"/api/google-staging/web/rph/jobs/{job_id}/download/pdf").status_code, 409)
        status = self.client.get(
            f"/api/google-staging/web/rph/jobs/{job_id}/status")
        self.assertEqual(status.json["status"], "prepared")

    def test_cross_site_issue_is_rejected(self):
        rejected = self.post("/api/google-staging/web/rph/issue", REQUEST,
                             origin="https://attacker.example")
        self.assertEqual(rejected.status_code, 403)
        self.assertEqual(self.jobs, {})

    def test_zero_credits_with_no_payment_cannot_create_job(self):
        self.credits = 0
        with patch("web.google_payment_store.web_payment_access",
                   return_value={"payment_access_active": False}):
            denied = self.post("/api/google-staging/web/rph/issue", REQUEST)
        self.assertEqual(denied.status_code, 403)
        self.assertEqual(self.jobs, {})
        self.assertEqual(self.debits, 0)


if __name__ == "__main__":
    unittest.main()
