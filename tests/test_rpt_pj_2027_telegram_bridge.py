import tempfile
import unittest
from pathlib import Path

from rpt_pj_2027_delivery import FILE_PATTERN, RPTAccessDenied
from rpt_pj_2027_telegram_bridge import (
    decode_callback, encode_callback, handle_download, visible_catalogue
)


class Bot:
    def __init__(self):
        self.sent = []

    def send_document(self, chat_id, handle):
        self.sent.append((chat_id, handle.name))
        return {"ok": True}


class TestTelegramBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        folder = self.root / "RPT_PJ_2027_DOCX"
        folder.mkdir()
        (folder / FILE_PATTERN.format(state="Johor", year=4)).write_bytes(b"fixture")

    def test_catalogue_only_installed(self):
        self.assertEqual(visible_catalogue(self.root), {"Johor": [4]})

    def test_callback_roundtrip_and_validation(self):
        self.assertEqual(decode_callback(encode_callback("Negeri Sembilan", 6)),
                         ("Negeri_Sembilan", 6))
        for invalid in ("rptpj27:Johor:4:paid", "rptpj27:../Johor:4",
                        "rptpj27:Johor:7", "rptpj27:Johor:4" + "x" * 100):
            with self.assertRaises(ValueError):
                decode_callback(invalid)

    def test_access_is_rechecked_on_each_download(self):
        bot = Bot()
        current = {"subscription_active": True}
        resolver_calls = []
        def resolver(user):
            resolver_calls.append(user)
            return current.copy()
        handle_download(bot, 123, self.root, "rptpj27:Johor:4",
                        user_id=321, access_resolver=resolver)
        current["subscription_active"] = False
        with self.assertRaises(RPTAccessDenied):
            handle_download(bot, 123, self.root, "rptpj27:Johor:4",
                            user_id=321, access_resolver=resolver)
        self.assertEqual(resolver_calls, [321, 321])
        self.assertEqual(len(bot.sent), 1)

    def test_only_explicit_true_flags_authorize(self):
        bot = Bot()
        with self.assertRaises(RPTAccessDenied):
            handle_download(bot, 123, self.root, "rptpj27:Johor:4",
                            user_id=321, access_resolver=lambda _: {"subscription_active": "true"})
        self.assertFalse(bot.sent)
        handle_download(bot, 123, self.root, "rptpj27:Johor:4",
                        user_id=321, access_resolver=lambda _: {"rakan_pembangun_active": True})
        self.assertEqual(len(bot.sent), 1)


if __name__ == "__main__":
    unittest.main()
