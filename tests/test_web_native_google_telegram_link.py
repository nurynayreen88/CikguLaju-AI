"""Native Google + Telegram link requires both signed Web sessions and consent.

Mocks only private backend data, never touches production/staging credits.
"""
import unittest
from unittest.mock import patch
from flask import Flask

from web.native_google_telegram_link_routes import bp
from web_v1_canonical_sessions import COOKIE as GOOGLE_COOKIE,issue_google_principal_ticket
from web_v1_telegram_auth_routes import COOKIE as TELEGRAM_COOKIE
from web_v1_sessions import issue_session_ticket

ACCOUNT="1a267083-8511-4587-a585-857fe35f4a14"
HOST="cikgulaju-web.onrender.com"
BASE="https://"+HOST
SECRET="native-google-link-unit-test-session-secret-long-enough"
UID=131321111
CFG={"origin":BASE,"supabase_url":"https://soxakntcanbycjoygrcx.supabase.co",
     "supabase_key":"sb_secret_mock_private_service_role_key_12345",
     "secret":SECRET}
OLD={"account_id":ACCOUNT,"login_id":"teacher@example.com",
     "legacy_telegram_user_id":None,"google_only_trial_remaining":8}
LINKED={**OLD,"legacy_telegram_user_id":UID,"google_only_trial_remaining":None}
TELEGRAM={"authenticated":True,"telegram_user_id":UID,"free_remaining":7}
AFTER={**TELEGRAM,"free_remaining":5}


class NativeAccountLinkTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.register_blueprint(bp)
        self.client=app.test_client()
        self.cfg=patch("web.native_google_telegram_link_routes.google_config",return_value=CFG)
        self.cfg.start()
        self.addCleanup(self.cfg.stop)

    def sign(self,google=True,telegram=True):
        if google:
            self.client.set_cookie(GOOGLE_COOKIE,issue_google_principal_ticket(ACCOUNT,SECRET),
                                   domain=HOST)
        if telegram:
            self.client.set_cookie(TELEGRAM_COOKIE,issue_session_ticket(UID,SECRET),
                                   domain=HOST)

    def preview(self):
        return self.client.get("/api/auth/google-native/link-preview",base_url=BASE)

    def link(self,body,origin=BASE):
        return self.client.post("/api/auth/google-native/link-telegram",
            json=body,base_url=BASE,
            headers={"Origin":origin,"Sec-Fetch-Site":"same-origin"})

    def test_link_page_requires_google_login_but_does_not_auto_merge(self):
        self.sign(google=True,telegram=False)
        with patch("web.native_google_telegram_link_routes._read_json") as write:
            res=self.client.get("/google-link-telegram",base_url=BASE)
        self.assertEqual(res.status_code,200)
        self.assertIn(b"Pautkan Google dan Telegram",res.data)
        self.assertIn(b"after_link_remaining",res.data)
        write.assert_not_called()

    def test_missing_either_proof_never_reads_credits(self):
        for google,telegram in ((False,False),(True,False),(False,True)):
            with self.subTest(google=google,telegram=telegram):
                self.client.delete_cookie(GOOGLE_COOKIE,domain=HOST)
                self.client.delete_cookie(TELEGRAM_COOKIE,domain=HOST)
                self.sign(google,telegram)
                with patch("web.native_google_telegram_link_routes.read_google_principal") as db:
                    self.assertEqual(self.preview().status_code,401)
                    db.assert_not_called()

    def test_preview_exact_shared_trial_reconciliation_without_write(self):
        self.sign()
        with (patch("web.native_google_telegram_link_routes.read_google_principal",
                    return_value=OLD) as google,
              patch("web.native_google_telegram_link_routes._lookup",
                    return_value=TELEGRAM) as telegram,
              patch("web.native_google_telegram_link_routes._read_json") as write):
            res=self.preview()
        self.assertEqual(res.status_code,200)
        self.assertEqual(res.json["google_remaining"],8)
        self.assertEqual(res.json["telegram_remaining"],7)
        self.assertEqual(res.json["after_link_remaining"],5)
        self.assertTrue(res.json["explicit_confirmation_required"])
        google.assert_called_once_with(CFG,ACCOUNT)
        telegram.assert_called_once_with(CFG,UID)
        write.assert_not_called()

    def test_link_requires_valid_same_origin_and_explicit_consent(self):
        self.sign()
        body={"confirm":True,"google_remaining":8,"telegram_remaining":7}
        with (patch("web.native_google_telegram_link_routes.read_google_principal",
                    return_value=OLD),
              patch("web.native_google_telegram_link_routes._lookup",
                    return_value=TELEGRAM),
              patch("web.native_google_telegram_link_routes._read_json") as write):
            self.assertEqual(self.link(body,"https://evil.example").status_code,403)
            self.assertEqual(self.link({**body,"confirm":False}).status_code,400)
            self.assertEqual(self.link({**body,"telegram_remaining":9}).status_code,409)
            write.assert_not_called()

    def test_confirmed_link_uses_exact_privileged_rpc_then_verifies_readback(self):
        self.sign()
        body={"confirm":True,"google_remaining":8,"telegram_remaining":7}
        from web.native_google_telegram_link_routes import PROD_SUPABASE
        with (patch("web.native_google_telegram_link_routes.read_google_principal",
                    side_effect=[OLD,LINKED]),
              patch("web.native_google_telegram_link_routes._lookup",
                    side_effect=[TELEGRAM,AFTER]),
              patch("web.native_google_telegram_link_routes._read_json",
                    return_value={"linked":True,"replayed":False,
                                  "telegram_user_id":UID,"telegram_remaining_after":5}) as commit):
            response=self.link(body)
        self.assertEqual(response.status_code,200)
        self.assertTrue(response.json["linked"])
        self.assertEqual(response.json["telegram_remaining"],5)
        req=commit.call_args.args[0]
        self.assertEqual(req.full_url,PROD_SUPABASE+
           "/rest/v1/rpc/link_native_google_telegram_principal")
        import json
        payload=json.loads(req.data)
        self.assertEqual(payload,{"p_principal_id":ACCOUNT,
          "p_telegram_user_id":UID,"p_merge_confirmed":True,
          "p_expected_google_remaining":8,"p_expected_telegram_remaining":7})
        self.assertEqual(response.headers["Cache-Control"],"no-store, private")

    def test_failed_postcommit_readback_does_not_claim_link_success(self):
        self.sign()
        body={"confirm":True,"google_remaining":8,"telegram_remaining":7}
        with (patch("web.native_google_telegram_link_routes.read_google_principal",
                    side_effect=[OLD,OLD]),
              patch("web.native_google_telegram_link_routes._lookup",
                    side_effect=[TELEGRAM,TELEGRAM]),
              patch("web.native_google_telegram_link_routes._read_json",
                    return_value={"linked":True,"telegram_user_id":UID,
                                  "telegram_remaining_after":5})):
            response=self.link(body)
        self.assertEqual(response.status_code,503)
        self.assertIn("Semak status",response.json["error"])

    def test_already_linked_account_does_not_call_merge_rpc(self):
        self.sign()
        with (patch("web.native_google_telegram_link_routes.read_google_principal",
                    return_value=LINKED),
              patch("web.native_google_telegram_link_routes._lookup",
                    return_value=AFTER),
              patch("web.native_google_telegram_link_routes._read_json") as write):
            info=self.preview()
            res=self.link({"confirm":True,"google_remaining":0,
                           "telegram_remaining":5})
        self.assertEqual(info.status_code,200)
        self.assertTrue(info.json["linked"])
        self.assertEqual(res.status_code,200)
        self.assertTrue(res.json["already_linked"])
        write.assert_not_called()

    def test_unrelated_telegram_session_cannot_take_over_google_link(self):
        self.sign()
        with (patch("web.native_google_telegram_link_routes.read_google_principal",
                    return_value={**LINKED,"legacy_telegram_user_id":987654321}),
              patch("web.native_google_telegram_link_routes._lookup",
                    return_value=TELEGRAM),
              patch("web.native_google_telegram_link_routes._read_json") as write):
            res=self.preview()
        self.assertEqual(res.status_code,409)
        write.assert_not_called()


if __name__=="__main__":
    unittest.main()
