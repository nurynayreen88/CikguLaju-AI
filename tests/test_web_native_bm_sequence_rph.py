"""Web BM must use true Telegram verified_pdp_sequence and signed RPH renderer."""
import io
import unittest
from pathlib import Path
from unittest.mock import patch

from flask import Flask
from web.native_telegram_bm_rph_client import _selection
from web.unified_rph_web import create_blueprint

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "b" + "a" * 24


class WebBMNativeTests(unittest.TestCase):
    def setUp(self):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        self.client = app.test_client()
        self.query = {"year": "2", "subject":"BM",
                      "unit": "Keluargaku Sayang", "lesson":TOKEN}

    def test_exact_opaque_token_not_rpt_row_id(self):
        self.assertEqual(_selection(2,"Keluargaku Sayang",TOKEN)["lesson"],TOKEN)
        for bad in ("123","b"+"z"*24,"e-2-001","", "b"*25):
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                _selection(2,"Keluargaku Sayang",bad)

    @patch("web.native_telegram_bm_rph_client.verified_native_bm_available", return_value=True)
    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123},None))
    def test_available_native_bm_uses_actual_source(self, *_):
        r=self.client.get("/api/web/rph/availability", query_string=self.query)
        self.assertEqual(r.status_code,200,r.get_json())
        self.assertEqual(r.get_json(),{"available":True,"generator":"telegram-native"})

    @patch("web.native_telegram_bm_rph_client.verified_native_bm_available", return_value=True)
    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id":123},None))
    def test_paid_web_bm_word_routes_to_native_telegram(self, *_):
        fake=io.BytesIO(b"PK\x03\x04"+b"docx"*350)
        with patch("web.native_telegram_bm_rph_client.request_native_bm_rph",
                   return_value=fake) as mock:
            r=self.client.get("/api/web/rph/word",query_string=self.query)
        self.assertEqual(r.status_code,200,r.data[:100])
        self.assertEqual(r.headers["X-RPH-Generator"],"telegram-native")
        self.assertEqual(r.headers["X-RPH-Access-Mode"],"paid")
        mock.assert_called_once()
        self.assertEqual(mock.call_args.args[0]["source"],"telegram-native-bm-pdp")
        self.assertEqual(mock.call_args.args[0]["lesson"],TOKEN)
        self.assertEqual(mock.call_args.args[1],"word")

    def test_browser_uses_exact_bm_hierarchy_before_final_pdp(self):
        s=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn('"bm-themes"',s)
        self.assertIn('"bm-units"',s)
        self.assertIn('"bm-topics"',s)
        self.assertIn('"bm-pdp"',s)
        self.assertIn('disabled=el.options.length<=1',s)


if __name__=="__main__":
    unittest.main()
