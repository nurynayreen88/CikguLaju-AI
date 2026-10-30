"""Regression tests for conservative RPT PJ 2027 preflight gates."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.preflight_rpt_pj_2027 import preflight


class RPTPreflightRegression(unittest.TestCase):
    def test_missing_archive_and_assets_cannot_release(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = preflight(root / "missing.zip", root / "missing_assets")
            self.assertFalse(result["archive_verified"])
            self.assertFalse(result["assets_installed"])
            self.assertFalse(result["release_ready"])
            self.assertTrue(result["problems"])

    def test_installed_assets_alone_do_not_certify_production(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with patch("scripts.preflight_rpt_pj_2027.list_available") as listing:
                from rpt_pj_2027_delivery import STATES, YEARS
                listing.return_value = [
                    {"negeri": state.replace("_", " "), "tahun": year}
                    for state in STATES for year in YEARS
                ]
                result = preflight(root / "missing.zip", root)
            self.assertEqual(result["installed_count"], 48)
            self.assertTrue(result["assets_installed"])
            self.assertFalse(result["telegram_registered"])
            self.assertFalse(result["production_deployed"])
            self.assertFalse(result["release_ready"])


if __name__ == "__main__":
    unittest.main()
