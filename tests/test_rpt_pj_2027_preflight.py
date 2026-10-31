import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rpt_pj_2027_telegram_bridge import encode_callback, handle_download
from rpt_pj_2027_delivery import RPTAccessDenied
from scripts.preflight_rpt_pj_2027 import preflight


class TestReleasePreflight(unittest.TestCase):
    def test_missing_assets_never_claim_release_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            report = preflight(root / "missing.zip", root / "empty")
            self.assertFalse(report["archive_verified"])
            self.assertFalse(report["assets_installed"])
            self.assertFalse(report["release_ready"])
            self.assertTrue(report["problems"])

    def test_verified_archive_still_requires_live_integration(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            archive = root / "archive.zip"
            archive.write_bytes(b"fixture")
            with (
                patch("scripts.preflight_rpt_pj_2027.hashlib.sha256") as sha,
                patch("scripts.preflight_rpt_pj_2027.verify", return_value=[]),
            ):
                from scripts.preflight_rpt_pj_2027 import EXPECTED_ARCHIVE_SHA256
                sha.return_value.hexdigest.return_value = EXPECTED_ARCHIVE_SHA256
                report = preflight(archive, root)
            self.assertTrue(report["archive_verified"])
            self.assertFalse(report["release_ready"])
            self.assertIn("Telegram app.py integration not verified", report["problems"])

    def test_boolean_year_not_accepted(self):
        with self.assertRaises(ValueError):
            encode_callback("Johor", True)

    def test_missing_resolver_is_fail_closed(self):
        with self.assertRaises(RPTAccessDenied):
            handle_download(object(), 123, "/missing", "rptpj27:Johor:4",
                            user_id=456, access_resolver=None)


if __name__ == "__main__":
    unittest.main()
