"""Unit tests for the opt-in PJPK activity adapter."""
import unittest
from unittest.mock import patch
from pjpk_activity_adapter_v2666 import prepare_pjpk_rph, install_pjpk_activity_adapter

class AdapterTests(unittest.TestCase):
    def setUp(self):
        self.base = dict(subject="Pendidikan Jasmani", year="2", topic="Teroka Ruang")
        self.verified = dict(self.base, sk_code="1.1", sp_code="1.1.1",
                             sk_text="Kemahiran", sp_text="Melakukan kemahiran",
                             _pjpk_standards_complete_v2659=True)
    def test_verified_plan_attached(self):
        with patch("pjpk_activity_adapter_v2666.enrich_pjpk_rph", return_value=self.verified):
            result = prepare_pjpk_rph(self.base, lambda: None)
        self.assertTrue(result["_pjpk_activity_verified_v2666"])
        self.assertEqual(len(result["_pjpk_activity_phases_v2666"]), 4)
        self.assertNotIn("_pjpk_activity_phases_v2666", self.base)
    def test_unverified_fallback(self):
        with patch("pjpk_activity_adapter_v2666.enrich_pjpk_rph", return_value=self.base):
            self.assertEqual(prepare_pjpk_rph(self.base, lambda: None), self.base)
    def test_conflicting_standards_not_overwritten(self):
        original = dict(self.base, sp_code="2.2.2")
        with patch("pjpk_activity_adapter_v2666.enrich_pjpk_rph", return_value=self.verified):
            self.assertEqual(prepare_pjpk_rph(original, lambda: None), original)
    def test_other_subject_not_modified(self):
        original = dict(subject="Matematik", year="2", topic="Nombor")
        self.assertEqual(prepare_pjpk_rph(original, lambda: None), original)
    def test_wrapper_idempotent(self):
        calls = []
        namespace = {"_db": lambda: None, "_local_rph_text": lambda x: calls.append(x) or "ok"}
        self.assertTrue(install_pjpk_activity_adapter(namespace))
        first = namespace["_local_rph_text"]
        self.assertTrue(install_pjpk_activity_adapter(namespace))
        self.assertIs(first, namespace["_local_rph_text"])
        self.assertEqual(first(dict(subject="Matematik")), "ok")
        self.assertEqual(len(calls), 1)

if __name__ == "__main__":
    unittest.main()
