"""Staging tests for verified PJPK RPH integration; no live DB or app import."""
import unittest
from unittest.mock import patch

from pjpk_rph_integration_v2664 import install_pjpk_bridge

class PJPKIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.calls = []
        def legacy(selection, *args, **kwargs):
            self.calls.append(selection)
            return "legacy-rph"
        self.namespace = {"_local_rph_text": legacy, "_db": lambda: None}
        self.assertTrue(install_pjpk_bridge(self.namespace))

    def test_verified_pjpk_uses_composer(self):
        with patch("pjpk_rph_integration_v2664.render_verified_pjpk_text", return_value="verified-pjpk-rph") as compose:
            result = self.namespace["_local_rph_text"]({"subject": "Pendidikan Jasmani", "year": "Tahun 1"})
        self.assertEqual(result, "verified-pjpk-rph")
        compose.assert_called_once()
        self.assertEqual(self.calls, [])

    def test_verified_pk_uses_composer(self):
        with patch("pjpk_rph_integration_v2664.render_verified_pjpk_text", return_value="verified-pk-rph") as compose:
            result = self.namespace["_local_rph_text"]({"subject": "Pendidikan Kesihatan", "year": "Tahun 6"})
        self.assertEqual(result, "verified-pk-rph")
        compose.assert_called_once()

    def test_missing_verified_mapping_falls_back_without_fabricating_composer_output(self):
        with patch("pjpk_rph_integration_v2664.render_verified_pjpk_text", return_value=None):
            result = self.namespace["_local_rph_text"]({"subject": "Pendidikan Jasmani", "year": "Tahun 2"})
        self.assertEqual(result, "legacy-rph")
        self.assertEqual(len(self.calls), 1)

    def test_unrelated_subject_never_calls_composer(self):
        with patch("pjpk_rph_integration_v2664.render_verified_pjpk_text") as compose:
            result = self.namespace["_local_rph_text"]({"subject": "Matematik"})
        self.assertEqual(result, "legacy-rph")
        compose.assert_not_called()

    def test_installation_is_idempotent(self):
        installed = self.namespace["_local_rph_text"]
        self.assertTrue(install_pjpk_bridge(self.namespace))
        self.assertIs(self.namespace["_local_rph_text"], installed)

if __name__ == "__main__":
    unittest.main()
