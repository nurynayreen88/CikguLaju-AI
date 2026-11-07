"""Google-only native Word/PDF route controls, before any live activation."""
import unittest
from unittest.mock import patch
from flask import Flask, jsonify

from web.native_google_rph_routes import bp, _ticket, _verify

SECRET="canonical-google-rph-private-session-secret-32chars"
ACCOUNT="1a267083-8511-4587-a585-857fe35f4a14"
JOB="c44b79a0-6bda-4d1d-9ff0-14ec72c046c7"
DIGEST="a"*64
CFG={"origin":"https://cikgulaju-web.onrender.com","secret":SECRET}
PICK={"year":3,"subject":"ENGLISH","unit":"Unit One",
      "lesson":"e-3-003","component":None}
TEACHER={"class":"3 Amanah","date":"2026-11-07",
         "time":"08:00 - 09:00","students":"28"}
BODY={"selection":PICK,"teacher":TEACHER}
ACTOR={"principal":{"account_id":ACCOUNT,"legacy_telegram_user_id":None},
       "access":{"rph_access_mode":"trial","rph_trial_remaining":8}}


class NativeGoogleRPHTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(bp)
        self.client=app.test_client()
        self.base=CFG["origin"]
        auth=patch("web.native_google_rph_routes._actor",return_value=(CFG,ACTOR,None))
        auth.start();self.addCleanup(auth.stop)

    def post(self,path,body,origin=None):
        return self.client.post(path,json=body,base_url=self.base,
                headers={"Origin":origin or self.base,
                         "Sec-Fetch-Site":"same-origin"})

    def test_native_google_selector_is_available_only_for_verified_account(self):
        with patch("web.native_google_rph_routes.prepare") as db:
            reply=self.client.get("/google-rph",base_url=self.base)
        self.assertEqual(reply.status_code,200)
        self.assertIn(b"Jana Bahan",reply.data)
        self.assertIn(b"RPH Word",reply.data)
        db.assert_not_called()

    def test_completed_google_only_document_stays_available_after_linking(self):
        from web.native_google_rph_routes import _actor
        with (patch("web.native_google_rph_routes._actor",
                    return_value=(CFG,ACTOR,None)) as actor,
              patch("web.native_google_rph_routes.ready_download",
                    return_value=(b"%PDF-1.4\\n"+b"x"*600+b"\\n%%EOF",
                                  "application/pdf")) as download):
            reply=self.client.get("/api/auth/google-native/rph/jobs/"+JOB+
                "/download/pdf",base_url=self.base)
        self.assertEqual(reply.status_code,200)
        actor.assert_called_once_with(allow_linked=True)
        download.assert_called_once_with(CFG,ACCOUNT,JOB,"pdf")

    def test_signed_tickets_bind_principal_source_and_job(self):
        token=_ticket(ACCOUNT,JOB,DIGEST,SECRET,now=1000)
        self.assertEqual(_verify(token,ACCOUNT,DIGEST,SECRET,now=1200),JOB)
        self.assertIsNone(_verify(token,ACCOUNT,DIGEST,SECRET,now=4601))
        self.assertIsNone(_verify(token,JOB,DIGEST,SECRET,now=1100))
        self.assertIsNone(_verify(token,ACCOUNT,"b"*64,SECRET,now=1100))

    def test_disabled_native_google_rph_gate(self):
        with patch("web.native_google_rph_routes._actor",
                   return_value=(None,None,({"error":"disabled"},503))):
            self.assertEqual(self.client.get("/api/auth/google-native/rph/capabilities",
                                 base_url=self.base).status_code,503)

    def test_issue_requires_same_origin_and_never_debits_before_files(self):
        with (patch("web.native_google_rph_routes._pick",return_value=(PICK,TEACHER)),
              patch("web.native_google_rph_routes.selection_fingerprint",
                    return_value=DIGEST),
              patch("web.native_google_rph_routes.prepare",
                    return_value={"status":"prepared"}) as prepare):
            evil=self.post("/api/auth/google-native/rph/issue",BODY,
                           origin="https://evil.example")
            self.assertEqual(evil.status_code,403)
            prepare.assert_not_called()
            good=self.post("/api/auth/google-native/rph/issue",BODY)
        self.assertEqual(good.status_code,200)
        self.assertFalse(good.json["charged"])
        self.assertEqual(good.json["status"],"prepared")
        self.assertEqual(_verify(good.json["ticket"],ACCOUNT,DIGEST,SECRET),
                         good.json["job_id"])

    def test_exhausted_user_cannot_issue_again(self):
        no={**ACTOR,"access":{"rph_access_mode":"exhausted",
                               "rph_trial_remaining":0}}
        with (patch("web.native_google_rph_routes._actor",return_value=(CFG,no,None)),
              patch("web.native_google_rph_routes._pick",return_value=(PICK,TEACHER)),
              patch("web.native_google_rph_routes.prepare") as prepare):
            res=self.post("/api/auth/google-native/rph/issue",BODY)
        self.assertEqual(res.status_code,403)
        prepare.assert_not_called()

    def test_repeat_completed_job_is_downloadable_without_regeneration(self):
        token=_ticket(ACCOUNT,JOB,DIGEST,SECRET)
        with (patch("web.native_google_rph_routes._pick",return_value=(PICK,TEACHER)),
              patch("web.native_google_rph_routes.selection_fingerprint",
                    return_value=DIGEST),
              patch("web.native_google_rph_routes.owned_job",
                    return_value={"status":"ready","selection_sha256":DIGEST,
                                  "remaining_after":8}) as read,
              patch("web.native_google_rph_routes.render_native_google_rph_bundle") as render,
              patch("web.native_google_rph_routes.publish") as publish):
            res=self.post("/api/auth/google-native/rph/generate",
                {**BODY,"ticket":token})
        self.assertEqual(res.status_code,200)
        self.assertTrue(res.json["already_ready"])
        self.assertEqual(res.json["remaining"],8)
        read.assert_called_once_with(CFG,ACCOUNT,JOB)
        render.assert_not_called()
        publish.assert_not_called()

    def test_generation_renders_once_then_atomic_publishes(self):
        ticket=_ticket(ACCOUNT,JOB,DIGEST,SECRET)
        with (patch("web.native_google_rph_routes._pick",return_value=(PICK,TEACHER)),
              patch("web.native_google_rph_routes.selection_fingerprint",
                    return_value=DIGEST),
              patch("web.native_google_rph_routes.owned_job",
                    return_value={"status":"prepared","selection_sha256":DIGEST}),
              patch("web.native_google_rph_routes.render_native_google_rph_bundle",
                    return_value={"word":b"fake docx","pdf":b"fake pdf"}) as render,
              patch("web.native_google_rph_routes.publish",
                    return_value={"status":"ready","allowed":True,
                                  "remaining":7}) as publish):
            res=self.post("/api/auth/google-native/rph/generate",
                {**BODY,"ticket":ticket})
        self.assertEqual(res.status_code,200)
        self.assertEqual(res.json["remaining"],7)
        render.assert_called_once()
        publish.assert_called_once_with(CFG,ACCOUNT,JOB,DIGEST,b"fake docx",b"fake pdf")

    def test_wrong_principal_ticket_never_renders(self):
        token=_ticket(JOB,JOB,DIGEST,SECRET)
        with (patch("web.native_google_rph_routes._pick",return_value=(PICK,TEACHER)),
              patch("web.native_google_rph_routes.selection_fingerprint",
                    return_value=DIGEST),
              patch("web.native_google_rph_routes.render_native_google_rph_bundle") as render):
            res=self.post("/api/auth/google-native/rph/generate",
                {**BODY,"ticket":token})
        self.assertEqual(res.status_code,403)
        render.assert_not_called()

    def test_private_ready_download_needs_same_canonical_owner(self):
        with patch("web.native_google_rph_routes.ready_download",
                   return_value=(b"%PDF-1.4\n"+b"x"*600+b"\n%%EOF",
                    "application/pdf")) as read:
            res=self.client.get("/api/auth/google-native/rph/jobs/"+JOB+
                                "/download/pdf",base_url=self.base)
        self.assertEqual(res.status_code,200)
        self.assertTrue(res.data.startswith(b"%PDF-"))
        read.assert_called_once_with(CFG,ACCOUNT,JOB,"pdf")

    def test_catalog_uses_exact_verified_existing_source(self):
        with patch("web.unified_rph_web.unit_options",
                   return_value=[{"value":"u1","label":"Unit One"}]) as units:
            res=self.client.get("/api/auth/google-native/rph/catalog?year=3&subject=ENGLISH",
                                base_url=self.base)
        self.assertEqual(res.status_code,200)
        self.assertEqual(res.json["items"][0]["value"],"u1")
        units.assert_called_once_with(3,"ENGLISH",component=None)


if __name__=="__main__":
    unittest.main()
