"""Web must use Telegram's grouped Sains/Matematik PdP source, not RPT weeks."""
import unittest
from pathlib import Path

from web.native_telegram_sequence_rph_client import _selection
from web.native_verified_rpt_rph_client import _selection as _rpt_selection

ROOT=Path(__file__).resolve().parents[1]


class WebNativePdPBridgeTests(unittest.TestCase):
    def test_math_science_use_opaque_telegram_unit_and_pdp_code(self):
        unit="u"+"a"*24
        self.assertEqual(_selection(2,"MATH",unit,"M2-PDP-007")["lesson"],
                         "M2-PDP-007")
        self.assertEqual(_selection(4,"SCIENCE",unit,"S4-PDP-011")["subject"],
                         "SCIENCE")
        for bad in (("MATH","1","M2-PDP-007"),
                    ("ENGLISH",unit,"M2-PDP-007"),
                    ("MATH",unit,"")):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                _selection(2,*bad)

    def test_web_rph_proxies_only_to_native_telegram_engine(self):
        code=(ROOT/"web"/"unified_rph_web.py").read_text("utf-8")
        self.assertIn('if subject in ("MATH", "SCIENCE"):',code)
        self.assertIn('verified_native_sequence_available(year, subject, unit, token)',code)
        self.assertIn('request_native_sequence_rph(selected, fmt)',code)
        self.assertIn('source": "telegram-native-pdp-sequence"',code)
        self.assertIn("authorize_rendered_document(",code)
        self.assertIn("lesson_tag",code)

    def test_math_science_navigation_from_active_telegram_only(self):
        code=(ROOT/"tools"/"run_web_v1_preview.py").read_text("utf-8")
        self.assertIn('if subject in ("MATH", "SCIENCE") and kind in ("units", "pdp"):',code)
        self.assertIn("list_native_units(year, subject)",code)
        self.assertIn("list_native_lessons(",code)
        self.assertIn("TELEGRAM_NATIVE_PDP_UNAVAILABLE",code)


if __name__=="__main__":
    unittest.main()
