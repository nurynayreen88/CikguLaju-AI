"""Read-only Web class suggestions must be bound to one signed-in Telegram account."""
import json
import unittest
from pathlib import Path
from unittest.mock import patch
from flask import Flask
from web.teacher_class_choices import normalize_class_names, get_existing_teacher_classes
from web_v1_telegram_auth_routes import auth_blueprint

ROOT = Path(__file__).resolve().parents[1]
CONFIG = {
    "CIKGULAJU_WEB_SESSION_SECRET": "test-only-session-secret" * 3,
    "account_backend": "supabase",
    "supabase_url": "https://unit-test.supabase.co",
    "supabase_key": "test-server-only-placeholder",
}

class _FakeResponse:
    def __init__(self, data):
        self.data=data
    def __enter__(self):
        return self
    def __exit__(self,*args):
        return False
    def read(self, size):
        return self.data[:size]

class _FakeOpener:
    def __init__(self, content):
        self.content=content
        self.request=None
    def open(self, request, timeout):
        self.request=request
        return _FakeResponse(self.content)

class SavedClassTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Flask(__name__)
        app.register_blueprint(auth_blueprint)
        cls.client=app.test_client()

    def test_normalization(self):
        self.assertEqual(normalize_class_names([
            "4 Bestari", " 4 bestari ", "5 Amanah", "<script>", "A\nB",
            "", None, "x"*41
        ]), ["4 Bestari","5 Amanah"])
        self.assertEqual(normalize_class_names({}), [])

    def test_server_side_lookup_uses_one_exact_telegram_id(self):
        opener=_FakeOpener(json.dumps([{"class_names":["3 Amanah","3 amanah","5A"]}]).encode())
        result=get_existing_teacher_classes(CONFIG["supabase_url"],CONFIG["supabase_key"],123456,opener=opener)
        self.assertEqual(result,["3 Amanah","5A"])
        self.assertIn("telegram_user_id=eq.123456",opener.request.full_url)
        self.assertNotIn("123457",opener.request.full_url)
        self.assertEqual(opener.request.get_method(),"GET")
        self.assertEqual(get_existing_teacher_classes(CONFIG["supabase_url"],CONFIG["supabase_key"],123456,
            opener=_FakeOpener(b"[]")),[])
        with self.assertRaises(ValueError):
            get_existing_teacher_classes("http://localhost", "key",123456,opener=opener)

    @patch("web_v1_telegram_auth_routes._config",return_value=CONFIG)
    @patch("web_v1_telegram_auth_routes.verify_session_ticket",return_value=None)
    def test_requires_signed_in_session(self,*_):
        self.assertEqual(self.client.get("/api/web/teacher/classes").status_code,401)

    @patch("web_v1_telegram_auth_routes._config",return_value=CONFIG)
    @patch("web_v1_telegram_auth_routes.verify_session_ticket",return_value=123456)
    @patch("web_v1_telegram_auth_routes._lookup",return_value={"telegram_user_id":9999})
    def test_rejects_other_users(self,*_):
        self.assertEqual(self.client.get("/api/web/teacher/classes").status_code,403)

    @patch("web.teacher_class_choices.get_existing_teacher_classes",return_value=["3 Amanah","5A"])
    @patch("web_v1_telegram_auth_routes._config",return_value=CONFIG)
    @patch("web_v1_telegram_auth_routes.verify_session_ticket",return_value=123456)
    @patch("web_v1_telegram_auth_routes._lookup",return_value={"telegram_user_id":123456})
    def test_authorized_teacher_sees_only_saved_classes(self,*_):
        resp=self.client.get("/api/web/teacher/classes")
        self.assertEqual(resp.status_code,200)
        self.assertEqual(resp.get_json(),{"items":["3 Amanah","5A"]})
        self.assertEqual(resp.headers["Cache-Control"],"no-store, private")
        self.assertEqual(self.client.get("/api/web/teacher/classes?telegram_user_id=9999").status_code,400)

    def test_saved_class_is_native_dropdown_with_manual_fallback(self):
        s=(ROOT/"web_v1_static_preview"/"index.html").read_text(encoding="utf8")
        self.assertIn('<select id="teacher-class">',s)
        self.assertIn('value="__other__"',s)
        self.assertIn('id="teacher-class-other"',s)
        self.assertIn('toggleTeacherClassOther()',s)
        self.assertIn('choices.add(new Option(clean,clean))',s)
        self.assertIn('loadTeacherClasses();return;',s)
        self.assertIn('if(!response.ok)return;',s)
        self.assertNotIn('list="saved-teacher-classes"',s)
        self.assertNotIn('id="teacher-class" type="text"',s)

if __name__=="__main__":
    unittest.main()
