"""Security checks for optional staging-only Google ↔ Telegram identity linking."""
import hashlib
import hmac
import time
import unittest
from unittest.mock import patch

from flask import Flask, jsonify

from web.google_telegram_link_staging_routes import bp
from web.provider_neutral_web_identity import (
    from_verified_google_account, from_verified_telegram_account,
    may_link_accounts,
)

ACCOUNT = "1a267083-8511-4587-a585-857fe35f4a14"
TELEGRAM_ID = 12345678987654
BOT_TOKEN = "123456:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdef"
CFG = {"origin": "https://staging.example.org", "secret": "x"*48,
       "supabase_url": "https://isolated.supabase.co",
       "staging_service_key": "sb_secret_"+"x"*40}
BOT = (BOT_TOKEN, "CikguLajuTestBot")


def telegram_payload(uid=TELEGRAM_ID, *, now=None):
    fields = {"id": str(uid), "auth_date": str(int(time.time() if now is None else now)),
              "first_name": "Guru"}
    check = "\n".join(f"{k}={v}" for k,v in sorted(fields.items()))
    # Same algorithm as the Telegram Login Widget. Not a real Telegram login.
    fields["hash"] = hmac.new(hashlib.sha256(BOT_TOKEN.encode()).digest(),
                              check.encode(), hashlib.sha256).hexdigest()
    return fields


class StagingLinkTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        app.config["TESTING"]=True
        app.register_blueprint(bp)
        self.client=app.test_client()
        self.account=ACCOUNT
        self.linked=None
        self.links=0
        self.patches=[
            patch("web.google_telegram_link_staging_routes._link_config",
                  return_value=(CFG,BOT)),
            patch("web.google_telegram_link_staging_routes._actor",
                  new=self.actor),
            patch("web.google_telegram_link_staging_routes._link_status",
                  new=self.status),
            patch("web.google_telegram_link_staging_routes._commit_link",
                  new=self.commit)
        ]
        for p in self.patches:
            p.start()
            self.addCleanup(p.stop)

    def actor(self):
        if self.account is None:
            return None,(jsonify({"error":"Google session required"}),401)
        return from_verified_google_account(
            self.account, {"account_id":self.account,"trial_remaining":9}),None

    def status(self, cfg, account):
        self.assertEqual(cfg,CFG)
        self.assertEqual(account,ACCOUNT)
        return {"linked":self.linked is not None,"staging_only":True,**(
            {"telegram_user_id":str(self.linked)} if self.linked else {})}

    def commit(self, cfg, account, telegram_id):
        self.assertEqual(cfg,CFG)
        self.assertEqual(account,ACCOUNT)
        if self.linked is not None and self.linked!=telegram_id:
            raise AssertionError("Unexpected account reassignment")
        self.linked=telegram_id
        self.links+=1
        return {"linked":True,"telegram_user_id":telegram_id,"staging_only":True}

    def submit(self, fields, *, origin=CFG["origin"]):
        return self.client.post(
            "/api/google-staging/link/telegram",
            json={"telegram_auth":fields},
            headers={"Origin":origin,"Sec-Fetch-Site":"same-origin"})

    def test_correct_widget_proof_links_only_staging_identity(self):
        state=self.client.get("/api/google-staging/link/telegram/status")
        self.assertEqual(state.status_code,200)
        self.assertFalse(state.json["linked"])
        self.assertFalse(state.json["entitlements_shared"])
        self.assertEqual(state.json["bot_username"],BOT[1])
        done=self.submit(telegram_payload())
        self.assertEqual(done.status_code,200,done.json)
        self.assertTrue(done.json["linked"])
        self.assertFalse(done.json["entitlements_shared"])
        self.assertEqual(done.json["telegram_user_id"],str(TELEGRAM_ID))
        self.assertEqual(self.links,1)

    def test_duplicate_submit_is_idempotent_at_route_level(self):
        proof=telegram_payload()
        self.assertEqual(self.submit(proof).status_code,200)
        self.assertEqual(self.submit(proof).status_code,200)
        self.assertEqual(self.linked,TELEGRAM_ID)

    def test_signature_forgery_and_altered_id_rejected(self):
        forged=telegram_payload()
        forged["id"]=str(TELEGRAM_ID+1)
        self.assertEqual(self.submit(forged).status_code,403)
        self.assertIsNone(self.linked)
        self.assertEqual(self.submit({"id":str(TELEGRAM_ID),
            "auth_date":str(int(time.time())),"hash":"0"*64}).status_code,403)
        self.assertEqual(self.links,0)

    def test_expired_widget_signature_rejected(self):
        self.assertEqual(
            self.submit(telegram_payload(now=time.time()-125)).status_code,403)
        self.assertIsNone(self.linked)

    def test_cross_site_post_does_not_link(self):
        self.assertEqual(self.submit(telegram_payload(),
            origin="https://attacker.example").status_code,403)
        self.assertEqual(self.links,0)

    def test_google_session_required_for_page_status_and_post(self):
        self.account=None
        self.assertEqual(self.client.get("/google-staging-link-telegram").status_code,401)
        self.assertEqual(self.client.get(
            "/api/google-staging/link/telegram/status").status_code,401)
        self.assertEqual(self.submit(telegram_payload()).status_code,401)
        self.assertEqual(self.links,0)

    def test_feature_flag_default_off(self):
        with patch("web.google_telegram_link_staging_routes._link_config",return_value=None):
            self.assertEqual(self.client.get("/google-staging-link-telegram").status_code,503)
            self.assertEqual(self.submit(telegram_payload()).status_code,503)
        self.assertEqual(self.links,0)

    def test_both_verified_actors_are_required(self):
        google=from_verified_google_account(ACCOUNT, {
            "account_id":ACCOUNT,"trial_remaining":9})
        telegram=from_verified_telegram_account(TELEGRAM_ID,{
            "authenticated":True,"telegram_user_id":TELEGRAM_ID})
        self.assertTrue(may_link_accounts(
            google,telegram,both_sessions_verified=True))
        self.assertFalse(may_link_accounts(
            google,telegram,both_sessions_verified=False))


if __name__=="__main__":
    unittest.main()
