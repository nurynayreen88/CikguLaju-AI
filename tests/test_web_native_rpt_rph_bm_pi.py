"""No misleading Web RPH links: use only an exact Telegram master row."""
import unittest
from unittest.mock import Mock
from urllib.error import HTTPError

from web.native_verified_rpt_rph_client import (
    _selection, verified_rpt_available, NativeRPHUnavailable,
)


class VerifiedRPTClientTests(unittest.TestCase):
    def test_only_exact_supported_master_ids_allowed(self):
        expected = {"year":2,"subject":"BM","unit":"Unit Bahasa","lesson":102}
        self.assertEqual(_selection({**expected, "lesson":"102"}), expected)
        for bad in (
            {**expected,"subject":"MATH"},
            {**expected,"subject":"SCIENCE"},
            {**expected,"lesson":"e-2-001"},
            {**expected,"lesson":"01"},
            {**expected,"lesson":"1 OR 1=1"},
            {**expected,"unit":""},
            {**expected,"year":0},
        ):
            with self.subTest(bad=bad),self.assertRaises(ValueError):
                _selection(bad)

    def test_bm_pi_server_contract_has_no_local_rph_content(self):
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        code=(root/"web"/"unified_rph_web.py").read_text("utf-8")
        self.assertIn('if subject == "PI":',code)
        self.assertIn('verified_rpt_available(year, subject, unit, token)',code)
        self.assertIn('request_verified_rpt_rph(selected, fmt)',code)
        self.assertIn('TELEGRAM_RPT_RPH_NOT_READY',code)
        self.assertIn('authorize_rendered_document(',code)

    def test_pi_unit_menu_keeps_original_bidang_without_archive_choice(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        menu = (root / "tools" / "run_web_v1_preview.py").read_text("utf-8")
        self.assertIn('source.list_units(year, "PI")', menu)
        self.assertNotIn('original.append({"value": PI_PREMIUM_UNIT', menu)
        self.assertNotIn('return jsonify(pi_696_options(year))', menu)
        self.assertIn('PI_ARCHIVE_OPTION_RETIRED', menu)

    def test_old_pi_archive_link_is_rejected_before_quota(self):
        from pathlib import Path
        code = (Path(__file__).resolve().parents[1] /
                "web" / "unified_rph_web.py").read_text("utf-8")
        start = code.index('if subject == "PI" and unit == PI_PREMIUM_UNIT:')
        next_branch = code.index('if subject == "PI":', start)
        retired = code[start:next_branch]
        self.assertIn("PI_ARCHIVE_OPTION_RETIRED", retired)
        self.assertIn("return None", retired)
        self.assertNotIn('source": "pi-696-private-bundle"', retired)
        self.assertIn('verified_rpt_available(year, subject, unit, token)', code)

    def test_availability_fails_closed_if_source_unconfigured(self):
        from unittest.mock import patch
        with patch.dict("os.environ",{
            "CIKGULAJU_AUTHORITATIVE_API_URL":"",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":""
        }):
            with self.assertRaises(NativeRPHUnavailable):
                verified_rpt_available(2,"BM","Unit Bahasa","102")


if __name__=="__main__":
    unittest.main()
