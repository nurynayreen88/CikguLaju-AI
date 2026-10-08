import unittest
from pjpk_rph_quality_v2672 import refine_verified_pjpk_rph

class PJPKRefinementTests(unittest.TestCase):
    def sample(self, subject):
        return dict(source_verified=True, subject=subject, year="Tahun 3",
                    topic="Imbangan", sk="1.1 Standard", sp="1.1.1 Standard",
                    activities=[dict(heading=str(i), description="Aktiviti") for i in range(4)])

    def test_pj(self):
        original = self.sample("Pendidikan Jasmani")
        output = refine_verified_pjpk_rph(original)
        self.assertIn("keselamatan", output["assessment"])
        self.assertNotIn("objective", original)

    def test_pk(self):
        output = refine_verified_pjpk_rph(self.sample("Pendidikan Kesihatan"))
        self.assertIn("situasi", output["objective"])

    def test_unverified_rejected(self):
        item = self.sample("Pendidikan Jasmani")
        item["source_verified"] = False
        self.assertIsNone(refine_verified_pjpk_rph(item))

    def test_incomplete_rejected(self):
        item = self.sample("Pendidikan Jasmani")
        item["activities"] = []
        self.assertIsNone(refine_verified_pjpk_rph(item))

if __name__ == "__main__":
    unittest.main()
