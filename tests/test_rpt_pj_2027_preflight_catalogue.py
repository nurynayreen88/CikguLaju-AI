"""Release gate rejects duplicate or incomplete RPT asset catalogue entries."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rpt_pj_2027_delivery import STATES, YEARS
from scripts.preflight_rpt_pj_2027 import preflight


class RPTPreflightCatalogueIntegrityTests(unittest.TestCase):
    def test_duplicate_catalogue_entry_cannot_pass_asset_gate(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rows = [
                {"negeri": state.replace("_", " "), "tahun": year}
                for state in STATES for year in YEARS
            ]
            with patch("scripts.preflight_rpt_pj_2027.list_available",
                       return_value=rows + [rows[0]]):
                result = preflight(root / "missing.zip", root)
            self.assertFalse(result["assets_installed"])
            self.assertFalse(result["release_ready"])
            self.assertEqual(result["installed_count"], 48)

    def test_exact_catalogue_still_needs_archive_and_production_checks(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            rows = [
                {"negeri": state.replace("_", " "), "tahun": year}
                for state in STATES for year in YEARS
            ]
            with patch("scripts.preflight_rpt_pj_2027.list_available",
                       return_value=rows):
                result = preflight(root / "missing.zip", root)
            self.assertTrue(result["assets_installed"])
            self.assertFalse(result["release_ready"])


if __name__ == "__main__":
    unittest.main()
