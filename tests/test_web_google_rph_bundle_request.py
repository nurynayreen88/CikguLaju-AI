"""Regression gates for private Google staging RPH prepare/completion routes."""
import json
import unittest
from unittest.mock import patch, Mock

from flask import Flask
from web.google_rph_bundle_request import (
    bp, _make_ticket, _verify_ticket, _selection_and_teacher,
    NativeGoogleRPHNotReady, BundleCommitUnconfirmed,
)
from web.provider_neutral_web_identity import from_verified_google_account

ACCOUNT = "bcbbd9d1-8b4c-4d8c-bd56-2e00e19442af"
OTHER = "1a267083-8511-4587-a585-857fe35f4a14"
JOB = "a3d7e1bb-f5b2-4529-9d10-144e11831144"
SECRET = "test-staging-rph-secret-" + "x" * 48
CONF = {"secret": SECRET, "origin": "https://staging.example.test",
        "supabase_url": "https://eqrcjlnvcytkgazptbor.supabase.co",
        "staging_service_key": "sb_secret_" + "x"*42}
ACTOR = from_verified_google_account(
    ACCOUNT, {"account_id":ACCOUNT,"trial_remaining":10})
SELECTION = {"year":3, "subject":"ENGLISH", "component":"",
             "unit":"Unit One", "lesson":"e-3-001"}
TEACHER = {"class":"3 Amanah","date":"2026-11-07",
           "time":"08:00 - 09:00","students":"28"}
REQUEST = {"selection":SELECTION,"teacher":TEACHER}
LESSONS = [{"value":"e-3-001","label":"Lesson 001","lesson_no":1}]


class GoogleRPHRequestTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.config["TESTING"] = True
        app.register_blueprint(bp)
        self.client = app.test_client()
        patches = [
            patch("web.google_rph_bundle_request._enabled_config", return_value=CONF),
            patch("web.google_rph_bundle_request._enabled", return_value=True),
            patch("web.google_rph_bundle_request._actor", return_value=(ACTOR,None)),
            patch("web.unified_rph_web.pdp_options", return_value=LESSONS),
        ]
        for p in patches:
            p.start()
            self.addCleanup(p.stop)

    def post(self, path, obj, *, origin=None, headers=None):
        return self.client.post(path, json=obj, headers={
            "Origin": origin or CONF["origin"],
            "Sec-Fetch-Site": "same-origin", **(headers or {})})

    def ready_prepare(self):
        with patch("web.google_rph_bundle_request.server_generation_reference",
                   return_value=JOB), patch(
                 "web.google_rph_bundle_request.prepare_private_bundle",
                 return_value={"job_id":JOB,"status":"prepared"}) as prepare:
            res = self.post("/api/google-staging/web/rph/prepare", REQUEST)
        return res, prepare

    def test_prepare_only_allocates_server_owned_job_without_spending(self):
        response, prepare = self.ready_prepare()
        self.assertEqual(response.status_code, 201)
        self.assertFalse(response.json["trial_debited"])
        self.assertEqual(response.json["job_id"],JOB)
        self.assertEqual(_verify_ticket(response.json["job_ticket"],
                SECRET, ACCOUNT, _selection_and_teacher(REQUEST)[2]),JOB)
        self.assertEqual(prepare.call_count,1)
        self.assertIs(prepare.call_args.args[1],ACTOR)
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")
        self.assertNotIn("Authorization",response.headers)

    def test_same_job_completes_once_only_after_native_renderer(self):
        prepared, _ = self.ready_prepare()
        event=[]
        def render(*a,**kw):
            event.append("render")
            return {"word":b"word","pdf":b"pdf"}
        def publish(*a,**kw):
            event.append("publish")
            self.assertEqual(a[2],JOB)
            self.assertEqual(a[4:],(b"word",b"pdf"))
            return {"job_id":JOB,"status":"ready","allowed":True,"remaining":9}
        with (patch("web.google_rph_bundle_request.prepare_private_bundle",
                    return_value={"job_id":JOB,"status":"prepared"}),
              patch("web.google_rph_bundle_request.render_native_google_rph_bundle",
                    side_effect=render),
              patch("web.google_rph_bundle_request.publish_rendered_bundle",
                    side_effect=publish)):
            res=self.post("/api/google-staging/web/rph/complete",{
                "request": REQUEST,"job_ticket":prepared.json["job_ticket"]})
        self.assertEqual(res.status_code,200)
        self.assertEqual(event,["render","publish"])
        self.assertEqual(res.json["remaining"],9)
        self.assertTrue(res.json["downloads"]["pdf"].endswith("/download/pdf"))
        self.assertNotIn("document_manifest_sha256",res.json)

    def test_replay_skips_renderer_and_debit(self):
        prepared,_=self.ready_prepare()
        with (patch("web.google_rph_bundle_request.prepare_private_bundle",
                    return_value={"job_id":JOB,"status":"ready"}),
              patch("web.google_rph_bundle_request.render_native_google_rph_bundle") as render,
              patch("web.google_rph_bundle_request.publish_rendered_bundle") as publish):
            res=self.post("/api/google-staging/web/rph/complete",{
                "request":REQUEST,"job_ticket":prepared.json["job_ticket"]})
        self.assertEqual(res.status_code,200)
        self.assertTrue(res.json["replayed"])
        render.assert_not_called()
        publish.assert_not_called()

    def test_wrong_origin_missing_login_and_disabled_feature_rejected(self):
        url="/api/google-staging/web/rph/prepare"
        self.assertEqual(self.post(url,REQUEST,origin="https://evil.example").status_code,403)
        with patch("web.google_rph_bundle_request._actor",
                   return_value=(None,("Log masuk Google diperlukan",401))):
            self.assertEqual(self.post(url,REQUEST).status_code,401)
        with patch("web.google_rph_bundle_request._enabled",return_value=False), patch(
                "web.google_rph_bundle_request.prepare_private_bundle") as store:
            self.assertEqual(self.post(url,REQUEST).status_code,503)
            store.assert_not_called()
        res=self.client.post(url,data="{}",
                             headers={"Origin":CONF["origin"],
                                      "Sec-Fetch-Site":"cross-site"})
        self.assertEqual(res.status_code,403)

    def test_forged_expired_and_other_account_tickets_never_generate(self):
        prepared,_=self.ready_prepare()
        ticket=prepared.json["job_ticket"]
        digest=_selection_and_teacher(REQUEST)[2]
        self.assertIsNone(_verify_ticket(ticket,SECRET,OTHER,digest))
        self.assertIsNone(_verify_ticket(ticket,SECRET,ACCOUNT,"f"*64))
        self.assertIsNone(_verify_ticket(_make_ticket(SECRET,ACCOUNT,JOB,digest,now=100),
                                         SECRET,ACCOUNT,digest,now=1901))
        with patch("web.google_rph_bundle_request.render_native_google_rph_bundle") as native:
            for modified in (ticket[:-1]+"0",ticket.replace(JOB,OTHER)):
                res=self.post("/api/google-staging/web/rph/complete",{
                    "request":REQUEST,"job_ticket":modified})
                self.assertEqual(res.status_code,403)
            native.assert_not_called()

    def test_invalid_lesson_or_teacher_does_not_prepare_or_charge(self):
        with patch("web.google_rph_bundle_request.prepare_private_bundle") as store:
            malformed = [
                {"selection":{**SELECTION,"lesson":"not-in-source"},"teacher":TEACHER},
                {"selection":{**SELECTION,"year":True},"teacher":TEACHER},
                {"selection":{**SELECTION,"telegram_user_id":123},"teacher":TEACHER},
                {"selection":SELECTION,"teacher":{**TEACHER,"date":"2026-99-99"}},
            ]
            for body in malformed:
                self.assertEqual(self.post("/api/google-staging/web/rph/prepare",
                                           body).status_code,400)
            store.assert_not_called()

    def test_native_failure_does_not_start_upload_or_charge(self):
        prepared,_=self.ready_prepare()
        with (patch("web.google_rph_bundle_request.prepare_private_bundle",
                    return_value={"job_id":JOB,"status":"prepared"}),
              patch("web.google_rph_bundle_request.render_native_google_rph_bundle",
                    side_effect=NativeGoogleRPHNotReady("offline")),
              patch("web.google_rph_bundle_request.publish_rendered_bundle") as publish):
            res=self.post("/api/google-staging/web/rph/complete",{
                "request":REQUEST,"job_ticket":prepared.json["job_ticket"]})
            self.assertEqual(res.status_code,503)
            self.assertIn("tidak ditolak",res.json["error"])
            publish.assert_not_called()

    def test_ambiguous_commit_never_claims_credit_unchanged(self):
        prepared,_=self.ready_prepare()
        with (patch("web.google_rph_bundle_request.prepare_private_bundle",
                    return_value={"job_id":JOB,"status":"prepared"}),
              patch("web.google_rph_bundle_request.render_native_google_rph_bundle",
                    return_value={"word":b"w","pdf":b"p"}),
              patch("web.google_rph_bundle_request.publish_rendered_bundle",
                    side_effect=BundleCommitUnconfirmed("timeout"))):
            res=self.post("/api/google-staging/web/rph/complete",{
                "request":REQUEST,"job_ticket":prepared.json["job_ticket"]})
        self.assertEqual(res.status_code,503)
        self.assertEqual(res.json["job_id"],JOB)
        self.assertNotIn("remaining",res.json)
        self.assertNotIn("trial_debited",res.json)

    def test_owner_bound_status_only_links_ready_job(self):
        url=f"/api/google-staging/web/rph/jobs/{JOB}/status"
        with patch("web.google_rph_bundle_request._ready_job",return_value={
                "id":JOB,"status":"prepared"}) as read:
            pending=self.client.get(url)
        self.assertEqual(pending.status_code,200)
        self.assertNotIn("downloads",pending.json)
        read.assert_called_once()
        with patch("web.google_rph_bundle_request._ready_job",return_value={
                "id":JOB,"status":"ready"}):
            ready=self.client.get(url)
        self.assertEqual(ready.status_code,200)
        self.assertIn("pdf",ready.json["downloads"])
        with patch("web.google_rph_bundle_request._ready_job",return_value=None):
            self.assertEqual(self.client.get(url).status_code,404)
        self.assertEqual(self.client.get(url+"?account_id="+OTHER).status_code,400)


if __name__ == "__main__":
    unittest.main()
