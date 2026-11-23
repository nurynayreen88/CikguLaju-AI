"""Regression tests: Telegram account receipt falls back to trusted admin chat."""
import json
import os
import unittest
from io import BytesIO
from unittest.mock import patch
from urllib.error import HTTPError

from web.web_payment_routes import _receipt_destinations, _telegram_document, ProfileUnavailable

CONF={"supabase_url":"https://unit.supabase.co","supabase_key":"server-secret-key-for-test-only"}
RECEIPT=b"%PDF-"+b"x"*1400

class Reply:
    status=200
    def __init__(self, destination):
        self.destination=destination
    def __enter__(self): return self
    def __exit__(self,*args): return None
    def read(self,maxbytes):
        return json.dumps({"ok":True,"result":{
            "chat":{"id":self.destination},"message_id":42,
            "document":{"file_id":"private-file-id","file_unique_id":"u",
                        "mime_type":"application/pdf"}}).encode()

class TelegramTransport:
    def __init__(self): self.destinations=[]
    def open(self,req,timeout):
        raw=req.data
        import re
        hit=re.search(rb'name="chat_id"\r\n\r\n([0-9]+)\r\n',raw)
        if not hit:
            raise AssertionError("missing destination")
        dest=int(hit.group(1))
        self.destinations.append(dest)
        if dest==712:
            raise HTTPError("https://redacted.invalid",403,"blocked",{},BytesIO(b""))
        return Reply(dest)

class ReceiptFallbackTests(unittest.TestCase):
    def setUp(self):
        e=patch.dict(os.environ,{"CIKGULAJU_WEB_ADMIN_IDS":"901",
            "CIKGULAJU_WEB_BOT_TOKEN":
            "123456789:abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMN"})
        e.start()
        self.addCleanup(e.stop)

    def test_real_telegram_account_uses_admin_when_user_bot_chat_blocked(self):
        self.assertEqual(_receipt_destinations(712),[712,901])
        transport=TelegramTransport()
        proof=_telegram_document(CONF,712,RECEIPT,".pdf",opener=transport)
        self.assertEqual(transport.destinations,[712,901])
        self.assertEqual(proof["file_id"],"private-file-id")
        self.assertEqual(proof["admin_chat_id"],901)

    def test_normal_telegram_customer_chat_remains_first(self):
        class WorkingTransport:
            def open(self,req,timeout):
                return Reply(712)
        proof=_telegram_document(CONF,712,RECEIPT,".pdf",opener=WorkingTransport())
        self.assertIsNone(proof["admin_chat_id"])

    def test_email_account_only_uses_admin_and_no_synthetic_chat(self):
        self.assertEqual(_receipt_destinations(8000000000000000005),[901])

    def test_no_admin_fallback_keeps_original_telegram_and_email_fails_closed(self):
        with patch.dict(os.environ,{"CIKGULAJU_WEB_ADMIN_IDS":""}):
            self.assertEqual(_receipt_destinations(712),[712])
            with self.assertRaises(ProfileUnavailable):
                _receipt_destinations(8000000000000000005)

if __name__=="__main__":
    unittest.main()
