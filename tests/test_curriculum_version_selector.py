import unittest
from curriculum_version_selector import LEGACY, KP2027, curriculum_options, resolve_curriculum

class CurriculumSelectorTests(unittest.TestCase):
    def test_legacy_remains_default(self):
        self.assertEqual(curriculum_options()[0]["id"], LEGACY)
        self.assertTrue(curriculum_options()[0]["default"])
        self.assertTrue(resolve_curriculum()["enabled"])

    def test_kp2027_never_falls_back_to_old_mapping(self):
        self.assertEqual(resolve_curriculum(KP2027, "Tahun 1", "Matematik")["reason"], "SOURCE_MAPPING_NOT_VERIFIED")
        self.assertEqual(resolve_curriculum(KP2027, "Tahun 2", "Matematik", {("Tahun 2", "Matematik")})["reason"], "NOT_IN_2027_ROLLOUT")

    def test_only_explicitly_verified_scope_opens(self):
        self.assertTrue(resolve_curriculum(KP2027, "Tahun 1", "Matematik", {("Tahun 1", "Matematik")})["enabled"])
        self.assertFalse(resolve_curriculum(KP2027, "Tingkatan 1", "Matematik", {("Tahun 1", "Matematik")})["enabled"])

    def test_unknown_version_fails_closed(self):
        with self.assertRaises(ValueError):
            resolve_curriculum("unknown")

if __name__ == "__main__":
    unittest.main()
