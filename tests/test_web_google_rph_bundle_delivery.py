"""A completed staging Google RPH is downloadable only by its owner."""
from io import BytesIO
import json
import unittest
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

from flask import Flask
from web.google_rph_bundle_delivery import (
    bp, _ready_job, _private_file, _recent_ready_jobs, RPHDeliveryUnavailable)
from web.provider_neutral_web_identity import from_verified_google_account

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
OTHER = "c1351d2d-591d-4ae4-8c92-b0e14d2c3234"
JOB = "0ebc954f-85e1-4c06-b4d2-41a8bf811111"
CONF = {"supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co",
        "staging_service_key": "sb_secret_" + "x"*40,
        "secret": "test-" + "x"*45, "origin": "https://example.test"}
ACTOR = from_verified_google_account(
    ACCOUNT, {"account_id": ACCOUNT, "trial_remaining": 10})
ROW = {"id": JOB, "account_id": ACCOUNT, "status": "ready",
       "document_manifest_sha256": "a"*64}
PDF = b"%PDF-1.7\n" + b"x"*700 + b"\n%%EOF\n"


def word():
    b=BytesIO()
    with ZipFile(b,"w",ZIP_DEFLATED) as arc:
        arc.writestr("[Content_Types].xml", "<Types/>"*30)
        arc.writestr("word/document.xml", "<document>"+("x"*500)+"</document>")
    return b.getvalue().ljust(520,b" ")


class FakeReply:
    status=200
    def __init__(self,payload,mime="application/json"):
        self.data=payload
        self.headers={"Content-Type":mime}
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data[:n]


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.app=Flask(__name__)
        self.app.config["TESTING"]=True
        self.app.register_blueprint(bp)
        self.client=self.app.test_client()
        self.config_patch=patch(
            "web.google_web_catalog_staging._enabled_config",return_value=CONF)
        self.config_patch.start()
        self.addCleanup(self.config_patch.stop)

    def test_anonymous_cannot_download(self):
        r=self.client.get(f"/api/google-staging/web/rph/jobs/{JOB}/download/pdf")
        self.assertEqual(r.status_code,401)
        self.assertEqual(r.headers["Cache-Control"],"no-store, private")

    def test_private_storage_query_bound_to_signed_account(self):
        captures=[]
        def fake(req,timeout):
            captures.append(req)
            return FakeReply(json.dumps([ROW]).encode())
        result=_ready_job(CONF,ACTOR,JOB,transport=fake)
        self.assertEqual(result,ROW)
        self.assertIn("account_id=eq."+ACCOUNT,captures[0].full_url)
        self.assertIn("id=eq."+JOB,captures[0].full_url)
        self.assertNotIn("Authorization",dict(captures[0].header_items()))
        self.assertEqual(dict(captures[0].header_items())["Apikey"],CONF["staging_service_key"])

    def test_other_account_row_never_accepted(self):
        def fake(req,timeout):
            return FakeReply(json.dumps([{**ROW,"account_id":OTHER}]).encode())
        with self.assertRaises(RPHDeliveryUnavailable):
            _ready_job(CONF,ACTOR,JOB,transport=fake)

    def test_unknown_job_not_found(self):
        self.assertIsNone(_ready_job(
            CONF,ACTOR,JOB,transport=lambda req,timeout:FakeReply(b"[]")))

    def test_download_paths_are_private_and_canonical(self):
        for fmt,data in (("pdf",PDF),("word",word())):
            with self.subTest(fmt=fmt):
                captured=[]
                def fake(req,timeout):
                    captured.append(req)
                    return FakeReply(data,
                        "application/pdf" if fmt=="pdf" else
                        "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                result=_private_file(CONF,ACCOUNT,JOB,fmt,transport=fake)
                self.assertEqual(result,data)
                self.assertIn("/storage/v1/object/authenticated/web-rph-bundles-staging/",captured[0].full_url)
                self.assertIn(ACCOUNT+"/"+JOB,captured[0].full_url)

    def test_invalid_document_fails_closed(self):
        with self.assertRaises(RPHDeliveryUnavailable):
            _private_file(CONF,ACCOUNT,JOB,"pdf",
                transport=lambda req,timeout:FakeReply(b"<html>invalid</html>"*55,"application/pdf"))

    def test_prepared_job_never_releases_bytes(self):
        with (patch("web.google_rph_bundle_delivery._actor",return_value=(ACTOR,None)),
              patch("web.google_rph_bundle_delivery._ready_job",
                    return_value={**ROW,"status":"prepared"}) as state,
              patch("web.google_rph_bundle_delivery._private_file") as content):
            res=self.client.get(f"/api/google-staging/web/rph/jobs/{JOB}/download/pdf")
        self.assertEqual(res.status_code,409)
        state.assert_called_once()
        content.assert_not_called()

    def test_successful_ready_job_download_and_no_second_debit(self):
        with (patch("web.google_rph_bundle_delivery._actor",return_value=(ACTOR,None)),
              patch("web.google_rph_bundle_delivery._enabled_config",return_value=CONF),
              patch("web.google_rph_bundle_delivery._ready_job",return_value=ROW),
              patch("web.google_rph_bundle_delivery._private_file",return_value=PDF) as source):
            response=self.client.get(f"/api/google-staging/web/rph/jobs/{JOB}/download/pdf")
        self.assertEqual(response.status_code,200)
        self.assertEqual(response.data,PDF)
        self.assertIn("attachment",response.headers["Content-Disposition"])
        self.assertEqual(response.headers["X-RPH-Generator"],"telegram-native")
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")
        source.assert_called_once()
        # No quota RPC is called by this route; a retry gets the persisted file.

    def test_malformed_job_or_extra_query_rejected(self):
        with patch("web.google_rph_bundle_delivery._actor",return_value=(ACTOR,None)):
            for url in (
                "/api/google-staging/web/rph/jobs/bad/download/pdf",
                f"/api/google-staging/web/rph/jobs/{JOB}/download/pdf?account_id={OTHER}",
                f"/api/google-staging/web/rph/jobs/{JOB}/download/exe",
            ):
                with self.subTest(url=url):
                    self.assertEqual(self.client.get(url).status_code,400)


    def test_recent_download_list_is_read_only_and_owner_bound(self):
        ready = {**ROW, "ready_at": "2026-11-07T05:00:00+00:00"}
        captured = []
        def transport(req, timeout):
            captured.append(req)
            return FakeReply(json.dumps([ready]).encode())
        result = _recent_ready_jobs(CONF, ACTOR, transport=transport)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["job_id"], JOB)
        self.assertTrue(result[0]["downloads"]["pdf"].endswith(JOB+"/download/pdf"))
        self.assertIn("account_id=eq."+ACCOUNT, captured[0].full_url)
        self.assertIn("status=eq.ready", captured[0].full_url)
        self.assertEqual(captured[0].get_method(), "GET")
        self.assertEqual(_recent_ready_jobs(
            CONF, ACTOR, transport=lambda req,timeout:FakeReply(b"[]")), [])

    def test_recent_private_list_rejects_cross_account_or_unready_rows(self):
        ready = {**ROW, "ready_at": "2026-11-07T05:00:00+00:00"}
        for forged in ({**ready, "account_id": OTHER},
                       {**ready, "status": "prepared"},
                       {**ready, "document_manifest_sha256": None},
                       {**ready, "id": "invalid"}):
            with self.subTest(forged=forged), self.assertRaises(RPHDeliveryUnavailable):
                _recent_ready_jobs(CONF, ACTOR, transport=lambda req, timeout:
                                   FakeReply(json.dumps([forged]).encode()))

    def test_recent_http_requires_login_and_releases_no_files_or_quota(self):
        endpoint = "/api/google-staging/web/rph/recent"
        self.assertEqual(self.client.get(endpoint).status_code, 401)
        with (patch("web.google_rph_bundle_delivery._actor",
                    return_value=(ACTOR, None)),
              patch("web.google_rph_bundle_delivery._enabled_config",
                    return_value=CONF),
              patch("web.google_rph_bundle_delivery._recent_ready_jobs",
                    return_value=[{"job_id":JOB,"ready_at":"2026-11-07",
                                   "downloads":{"word":"a","pdf":"b"}}]) as history,
              patch("web.google_rph_bundle_delivery._private_file") as files):
            self.assertEqual(self.client.get(endpoint+"?account_id="+OTHER).status_code,400)
            response=self.client.get(endpoint)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.json["staging_only"])
            self.assertEqual(len(response.json["items"]),1)
            self.assertEqual(response.headers["Cache-Control"], "no-store, private")
            history.assert_called_once()
            files.assert_not_called()


if __name__ == "__main__":
    unittest.main()
