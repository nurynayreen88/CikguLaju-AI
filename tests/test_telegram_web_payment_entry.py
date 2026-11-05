"""Regression: Web Telegram link is additive, QR is read-only and token-protected."""
import base64
import json
import os
from types import SimpleNamespace
from unittest.mock import patch
import unittest

from flask import Flask
from web.telegram_payment_source import create_web_payment_source
from web.web_link_telegram import install, WEB_URL


class Reply:
    ok=True
    def __init__(self,payload): self.payload=payload
    def json(self): return self.payload


class TelegramLinkTests(unittest.TestCase):
    def test_web_url_preserves_existing_menu_and_referral(self):
        payload={"ok":True,"result":{"message_id":44,
            "reply_markup":{"inline_keyboard":[
                [{"text":"RPH","callback_data":"rph"}],
                [{"text":"Akaun","callback_data":"account"}],
                [{"text":"Referral","callback_data":"private_referral_home"}],
                [{"text":"Manual","callback_data":"manual_pengguna_pdf"}],
            ]}}}
        sent=[]
        rt=SimpleNamespace(API="https://api.telegram.org/bot-example",
          menu=lambda cid,show_persistent=False: Reply(payload),
          send=lambda *args:sent.append(args))
        with patch("web.web_link_telegram.requests.post",
                   return_value=Reply({"ok":True})) as write:
            self.assertTrue(install(rt))
            rt.menu(123)
        body=write.call_args.kwargs["json"]
        rows=body["reply_markup"]["inline_keyboard"]
        self.assertEqual(body["chat_id"],123)
        self.assertEqual([b["callback_data"] for row in rows for b in row
                          if "callback_data" in b],
                         ["rph","account","private_referral_home","manual_pengguna_pdf"])
        self.assertEqual(sum(b.get("url")==WEB_URL for row in rows for b in row),1)
        self.assertFalse(sent)
        with patch("web.web_link_telegram.requests.post",return_value=Reply({"ok":True})):
            self.assertTrue(install(rt))
        self.assertEqual(rt.CIKGULAJU_WEB_LINK_MENU_ACTIVE,True)


class PaymentCatalogTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__)
        self.rt=SimpleNamespace(
            CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE=True,
            DONATION_QR_B64=base64.b64encode(b"\xff\xd8\xff"+b"x"*1000).decode("ascii"))
        app.register_blueprint(create_web_payment_source(self.rt))
        self.client=app.test_client()
        self.env={"CIKGULAJU_AUTHORITATIVE_API_TOKEN":"a"*64,
                  "CIKGULAJU_SUPABASE_USER_RECORDS":"1"}

    def test_token_and_proof_first_gate(self):
        with patch.dict(os.environ,self.env):
            self.assertEqual(self.client.get("/internal/payment/v1/catalog").status_code,401)
            wrong=self.client.get("/internal/payment/v1/qr",
               headers={"Authorization":"Bearer "+"x"*64})
            self.assertEqual(wrong.status_code,401)
            self.rt.CIKGULAJU_PROOF_FIRST_PAYMENT_ACTIVE=False
            denied=self.client.get("/internal/payment/v1/catalog",
               headers={"Authorization":"Bearer "+"a"*64})
            self.assertEqual(denied.status_code,503)

    def test_read_only_uses_verified_duitnow_and_telegram_prices(self):
        with patch.dict(os.environ,self.env):
            h={"Authorization":"Bearer "+"a"*64}
            result=self.client.get("/internal/payment/v1/catalog",headers=h)
            self.assertEqual(result.status_code,200)
            plans={p["code"]:p["amount"] for p in result.json["plans"]}
            self.assertEqual(plans,{"rakan_pembangun":"10.00",
                                    "langganan_30_hari":"5.00"})
            qr=self.client.get("/internal/payment/v1/qr",headers=h)
            self.assertEqual(qr.status_code,200)
            self.assertEqual(qr.mimetype,"image/jpeg")
            self.assertIn("no-store",qr.headers["Cache-Control"])
            self.assertTrue(qr.data.startswith(b"\xff\xd8\xff"))
            self.assertEqual(list(self.client.application.view_functions).count(
                "telegram_web_payment_source.catalog"),1)


if __name__=="__main__":
    unittest.main()
