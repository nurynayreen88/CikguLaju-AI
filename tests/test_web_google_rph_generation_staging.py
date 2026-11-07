"""Google RPH staging issue/generate routes are fail-closed unless deliberately enabled."""
import json
import unittest
from unittest.mock import patch

from flask import Flask

from web.google_rph_generation_staging_routes import (
    bp, _token, _verify_ticket, _request_payload, _generator_config,
    selection_fingerprint)
from web.provider_neutral_web_identity import from_verified_google_account

ACCOUNT="1a267083-8511-4587-a585-857fe35f4a14"
JOB="dba021fa-9ff9-46d3-8b20-9e2b90dc5411"
SECRET="staging-separate-session-"+"x"*45
CFG={"supabase_url":"https://eqrcjlnvcytkgazptbor.supabase.co",
     "staging_service_key":"sb_secret_"+"x"*45,
     "secret":SECRET,
     "origin":"https://cikgulaju-google-payments-staging.onrender.com",
     "host":"cikgulaju-google-payments-staging.onrender.com"}
ACTOR=from_verified_google_account(ACCOUNT,{"account_id":ACCOUNT,"trial_remaining":10})
SELECT={"year":3,"subject":"ENGLISH","unit":"Unit One",
        "lesson":"e-3-003","component":None}
TEACHER={"class":"3 Amanah","date":"2026-11-07",
         "time":"08:00 - 09:00","students":"28"}
REQUEST={"selection":SELECT,"teacher":TEACHER}
DIGEST=selection_fingerprint(SELECT,TEACHER)


class GoogleGenerationStagingTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.config["TESTING"]=True
        app.register_blueprint(bp)
        self.client=app.test_client()

    def post(self,path,payload,origin=CFG["origin"]):
        return self.client.post(path, json=payload, headers={
            "Origin": origin, "Sec-Fetch-Site":"same-origin"})

    def test_feature_flag_off_by_default(self):
        with (patch("web.google_rph_generation_staging_routes._actor",
                    return_value=(ACTOR,None)),
              patch("web.google_rph_generation_staging_routes._generator_config",
                    return_value=None)):
            self.assertEqual(self.post("/api/google-staging/web/rph/issue",REQUEST).status_code,503)
            self.assertEqual(self.post("/api/google-staging/web/rph/generate",
                 {"selection":SELECT,"teacher":TEACHER,"ticket":"fake"}).status_code,503)
            cap=self.client.get("/api/google-staging/web/rph/capabilities")
            self.assertEqual(cap.status_code,200)
            self.assertFalse(cap.json["generation_enabled"])
            self.assertEqual(cap.headers["Cache-Control"],"no-store, private")

    def test_generator_flag_checks_private_backend(self):
        with patch.dict("os.environ", {"CIKGULAJU_GOOGLE_RPH_STAGING_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_URL":"https://cikgulaju-web.onrender.com",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*40}):
            with patch("web.google_rph_generation_staging_routes._enabled_config",
                       return_value=CFG):
                self.assertIsNone(_generator_config())

    def test_signed_ticket_expires_and_cannot_be_edited_or_reused_for_other_account(self):
        signed=_token(ACCOUNT,JOB,DIGEST,SECRET,issued=1000)
        self.assertEqual(_verify_ticket(signed,ACCOUNT,DIGEST,SECRET,now=1200),JOB)
        self.assertIsNone(_verify_ticket(signed,ACCOUNT,DIGEST,SECRET,now=5000))
        self.assertIsNone(_verify_ticket(signed,JOB,DIGEST,SECRET,now=1200))
        self.assertIsNone(_verify_ticket(signed,ACCOUNT,"f"*64,SECRET,now=1200))
        self.assertIsNone(_verify_ticket(signed[:-1]+"f",ACCOUNT,DIGEST,SECRET,now=1200))

    def test_selection_must_be_exact_standalone_lesson(self):
        with patch("web.unified_rph_web.pdp_options",
                    return_value=[{"value":"e-3-003"}]) as options:
            choice,teacher=_request_payload(REQUEST)
        self.assertEqual(choice,SELECT)
        self.assertEqual(teacher,TEACHER)
        options.assert_called_once_with(3,"ENGLISH","Unit One",component=None)
        with patch("web.unified_rph_web.pdp_options",return_value=[]):
            with self.assertRaises(ValueError):
                _request_payload(REQUEST)

    def test_issue_requires_same_origin_and_server_creates_job(self):
        with (patch("web.google_rph_generation_staging_routes._actor",
                    return_value=(ACTOR,None)),
              patch("web.google_rph_generation_staging_routes._generator_config",
                    return_value=CFG),
              patch("web.google_rph_generation_staging_routes._request_payload",
                    return_value=(SELECT,TEACHER)),
              patch("web.google_rph_generation_staging_routes.google_staging_account_profile",
                    return_value={"trial_remaining":10}),
              patch("web.google_rph_generation_staging_routes.prepare_private_bundle") as prepare):
            prepare.side_effect=lambda cfg,actor,job,selection:{"job_id":job,"status":"prepared"}
            bad=self.post("/api/google-staging/web/rph/issue",REQUEST,
                          origin="https://malicious.example")
            self.assertEqual(bad.status_code,403)
            okay=self.post("/api/google-staging/web/rph/issue",REQUEST)
            self.assertEqual(okay.status_code,200)
            self.assertFalse(okay.json["charged"])
            self.assertEqual(okay.json["status"],"prepared")
            self.assertIsNotNone(_verify_ticket(okay.json["ticket"],ACCOUNT,DIGEST,SECRET))

    def test_generate_only_from_valid_ticket_and_owner(self):
        signed=_token(ACCOUNT,JOB,DIGEST,SECRET)
        with (patch("web.google_rph_generation_staging_routes._actor",
                    return_value=(ACTOR,None)),
              patch("web.google_rph_generation_staging_routes._generator_config",
                    return_value=CFG),
              patch("web.google_rph_generation_staging_routes._request_payload",
                    return_value=(SELECT,TEACHER)),
              patch("web.google_rph_generation_staging_routes._ready_job",
                    return_value={"id":JOB,"account_id":ACCOUNT,"status":"prepared"}) as state,
              patch("web.google_rph_generation_staging_routes.render_native_google_rph_bundle",
                    return_value={"word":b"word","pdf":b"pdf"}) as render,
              patch("web.google_rph_generation_staging_routes.publish_rendered_bundle",
                    return_value={"status":"ready","allowed":True,
                                  "job_id":JOB,"remaining":9}) as publish):
            failed=self.post("/api/google-staging/web/rph/generate",
                {"ticket":"invalid","selection":SELECT,"teacher":TEACHER})
            self.assertEqual(failed.status_code,403)
            self.assertEqual(render.call_count,0)
            okay=self.post("/api/google-staging/web/rph/generate",
                {"ticket":signed,"selection":SELECT,"teacher":TEACHER})
            self.assertEqual(okay.status_code,200)
            self.assertEqual(okay.json["remaining"],9)
            self.assertTrue(okay.json["downloads"]["word"].endswith("/download/word"))
            self.assertEqual(render.call_count,1)
            self.assertEqual(publish.call_count,1)
            state.assert_called_once()

    def test_completed_retry_does_not_regenerate_or_recharge(self):
        signed=_token(ACCOUNT,JOB,DIGEST,SECRET)
        with (patch("web.google_rph_generation_staging_routes._actor",
                    return_value=(ACTOR,None)),
              patch("web.google_rph_generation_staging_routes._generator_config",
                    return_value=CFG),
              patch("web.google_rph_generation_staging_routes._request_payload",
                    return_value=(SELECT,TEACHER)),
              patch("web.google_rph_generation_staging_routes._ready_job",
                    return_value={"id":JOB,"status":"ready"}),
              patch("web.google_rph_generation_staging_routes.render_native_google_rph_bundle") as render,
              patch("web.google_rph_generation_staging_routes.publish_rendered_bundle") as charge):
            okay=self.post("/api/google-staging/web/rph/generate",
                {"ticket":signed,"selection":SELECT,"teacher":TEACHER})
            self.assertEqual(okay.status_code,200)
            self.assertTrue(okay.json["already_ready"])
            render.assert_not_called()
            charge.assert_not_called()

    def test_anonymous_cannot_request_credit(self):
        from unittest.mock import patch
        with patch("web.google_rph_generation_staging_routes._actor",
                   return_value=(None, ({"error":"unauthorized"},401))):
            r=self.post("/api/google-staging/web/rph/issue",REQUEST)
            self.assertEqual(r.status_code,401)


if __name__=="__main__":
    unittest.main()
