"""Authorization regression tests for private Web admin chat."""
import unittest
from unittest.mock import patch
from flask import Flask
from web.web_admin_chat_routes import bp

class ChatTests(unittest.TestCase):
    def setUp(self):
        app=Flask(__name__);app.register_blueprint(bp)
        self.client=app.test_client()
        self.conf={"supabase_url":"https://unit.supabase.co","supabase_key":"secret-key-for-tests-long-enough"}
    def test_user_reads_only_own_messages(self):
        with patch("web.web_admin_chat_routes._auth",return_value=(self.conf,712,None)), \
             patch("web.web_admin_chat_routes._db",return_value=[]) as db:
            response=self.client.get("/api/web/chat")
        self.assertEqual(response.status_code,200)
        self.assertEqual(db.call_args.args[2]["user_id"],"eq.712")
    def test_admin_endpoint_denies_regular_user(self):
        with patch("web.web_admin_chat_routes._auth",return_value=(self.conf,712,None)), \
             patch("web.web_admin_chat_routes.allowed_admin_ids",return_value={901}), \
             patch("web.web_admin_chat_routes._db") as db:
            self.assertEqual(self.client.get("/api/web/admin/chats").status_code,403)
            self.assertEqual(self.client.get("/api/web/admin/chats/8000000000000000005").status_code,403)
            db.assert_not_called()
    def test_user_cannot_spoof_sender_or_owner(self):
        with patch("web.web_admin_chat_routes._auth",return_value=(self.conf,712,None)), \
             patch("web.web_admin_chat_routes._db") as db:
            response=self.client.post("/api/web/chat",base_url="https://cikgulaju-web.onrender.com",
                headers={"Origin":"https://cikgulaju-web.onrender.com"},
                json={"message":"Hi","user_id":901})
            self.assertEqual(response.status_code,400)
            db.assert_not_called()
    def test_admin_can_initiate_chat_to_email_account(self):
        with patch("web.web_admin_chat_routes._auth",return_value=(self.conf,901,None)), \
             patch("web.web_admin_chat_routes.allowed_admin_ids",return_value={901}), \
             patch("web.web_admin_chat_routes._db",return_value=[{"id":1}]) as db:
            response=self.client.post("/api/web/admin/chats/8000000000000000005",
                base_url="https://cikgulaju-web.onrender.com",
                headers={"Origin":"https://cikgulaju-web.onrender.com"},
                json={"message":"Sila hantar resit asal"})
        self.assertEqual(response.status_code,201)
        self.assertEqual(db.call_args.kwargs["body"]["user_id"],8000000000000000005)
        self.assertEqual(db.call_args.kwargs["body"]["sender_role"],"admin")

if __name__=="__main__":unittest.main()
