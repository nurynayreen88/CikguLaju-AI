"""No-network tests for the optional Telegram manual button."""
from __future__ import annotations

import importlib.util
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase, main
from unittest.mock import patch

from web.manual_pengguna_telegram import BUTTON, SOURCE, build_pdf, install


class Response:
    ok = True

    def __init__(self, keyboard=None, good=True):
        self.keyboard = keyboard
        self.ok = good

    def json(self):
        if self.keyboard is not None:
            return {"ok": self.ok, "result": {
                "message_id": 200, "reply_markup": {
                    "inline_keyboard": self.keyboard}}}
        return {"ok": self.ok}


class Runtime:
    API = "https://example.invalid/telegram-bot"

    def __init__(self, invited=False):
        self.invited = invited
        self.sent = []
        self.documents = []
        self.delegated = []
        self.credit_remaining = 10
        self.keyboard = [
            [{"text": "📚 Sediakan Bahan PdP", "callback_data": "quick"}],
            [{"text": "👤 Profil Saya", "callback_data": "account"}],
            [{"text": "🏆 Rakan Pembangun", "callback_data": "pioneer_join"}],
        ]

    def _private_referral_member(self, uid):
        return {"enabled": self.invited} if self.invited else None

    def menu(self, uid, show_persistent=False):
        return Response(self.keyboard)

    def callback(self, uid, data):
        self.delegated.append((uid, data))
        return "old"

    def send(self, uid, text, buttons=None):
        self.sent.append((uid, text, buttons))
        return Response()

    def send_document(self, uid, path, caption):
        self.documents.append((uid, Path(path).name, caption))
        return Response()


class TestManualMenu(TestCase):
    def test_source_is_complete(self):
        content = SOURCE.read_text(encoding="utf-8")
        self.assertTrue(content.startswith("# CIKGULAJU AI"))
        for section in ("RPH HARI INI", "RPT 2027", "RESIT", "REFERRAL", "MASALAH LAZIM"):
            self.assertIn(section, content)

    def test_menu_is_public_and_preserves_other_buttons(self):
        rt = Runtime(invited=False)
        self.assertTrue(install(rt))
        with patch("web.manual_pengguna_telegram.requests.post", return_value=Response()) as post:
            rt.menu(102)
        markup = post.call_args.kwargs["json"]["reply_markup"]["inline_keyboard"]
        ids = [x["callback_data"] for row in markup for x in row]
        self.assertEqual(ids, ["quick", "account", BUTTON["callback_data"], "pioneer_join"])
        self.assertEqual(rt.keyboard[1][0]["callback_data"], "account")
        self.assertEqual(rt.credit_remaining, 10)

    def test_invited_referral_entry_remains(self):
        rt = Runtime(invited=True)
        install(rt)
        with patch("web.manual_pengguna_telegram.requests.post", return_value=Response()) as post:
            rt.menu(102)
        markup = post.call_args.kwargs["json"]["reply_markup"]["inline_keyboard"]
        ids = [x["callback_data"] for row in markup for x in row]
        self.assertEqual(ids.count("private_referral_home"), 1)
        self.assertEqual(ids.count(BUTTON["callback_data"]), 1)

    def test_no_duplicate_when_original_response_already_has_manual(self):
        rt = Runtime()
        rt.keyboard.insert(2, [dict(BUTTON)])
        install(rt)
        with patch("web.manual_pengguna_telegram.requests.post") as post:
            rt.menu(102)
        post.assert_not_called()

    def test_other_callbacks_unchanged(self):
        rt = Runtime()
        install(rt)
        self.assertEqual(rt.callback(102, "pioneer_join"), "old")
        self.assertEqual(rt.delegated, [(102, "pioneer_join")])

    def test_menu_edit_failure_has_a_usable_fallback(self):
        rt = Runtime()
        install(rt)
        with patch("web.manual_pengguna_telegram.requests.post", return_value=Response(good=False)):
            rt.menu(102)
        self.assertEqual(rt.sent[-1][2][0][0]["callback_data"], BUTTON["callback_data"])

    def test_pdf_callback_uses_no_credit_or_payment(self):
        rt = Runtime()
        install(rt)
        with patch("web.manual_pengguna_telegram.build_pdf", side_effect=lambda out: Path(out)):
            result = rt.callback(102, BUTTON["callback_data"])
        self.assertIsInstance(result, Response)
        self.assertEqual(len(rt.documents), 1)
        self.assertEqual(rt.documents[0][0], 102)
        self.assertTrue(rt.documents[0][1].endswith(".pdf"))
        self.assertEqual(rt.credit_remaining, 10)

    def test_pdf_failure_has_retry(self):
        rt = Runtime()
        install(rt)
        with patch("web.manual_pengguna_telegram.build_pdf", side_effect=OSError("not mounted")):
            rt.callback(102, BUTTON["callback_data"])
        self.assertEqual(rt.documents, [])
        self.assertEqual(rt.sent[-1][2][0][0]["callback_data"], BUTTON["callback_data"])

    def test_install_twice_is_safe(self):
        rt = Runtime()
        self.assertTrue(install(rt))
        first = rt.menu
        self.assertTrue(install(rt))
        self.assertIs(first, rt.menu)

    def test_real_pdf_can_be_built(self):
        if importlib.util.find_spec("reportlab") is None:
            self.skipTest("reportlab not installed in this test runtime")
        with TemporaryDirectory() as folder:
            file = build_pdf(Path(folder) / "manual.pdf")
            self.assertGreater(file.stat().st_size, 4000)
            self.assertEqual(file.open("rb").read(5), b"%PDF-")
            if importlib.util.find_spec("pypdf"):
                from pypdf import PdfReader
                reader = PdfReader(str(file))
                self.assertGreaterEqual(len(reader.pages), 2)
                text = " ".join(p.extract_text() or "" for p in reader.pages)
                self.assertIn("MANUAL PENGGUNA", text)
                self.assertIn("RPH HARI INI", text)


if __name__ == "__main__":
    main()
