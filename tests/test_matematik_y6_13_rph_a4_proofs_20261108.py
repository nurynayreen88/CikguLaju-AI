"""Every exported Maths Y6 review proof must correspond to one isolated source draft."""
import unittest
from tools.build_matematik_y6_staging_rph_a4_20261108 import CANDIDATES, load_drafts

class Maths13StandaloneReviewProofs(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.lessons=load_drafts()

    def test_exactly_thirteen_distinct_source_grounded_drafts(self):
        self.assertEqual(len(self.lessons),13)
        self.assertEqual({x.code for x in self.lessons},set(CANDIDATES))
        self.assertEqual(len([d for d in self.lessons if d.code.startswith("FIN")]),3)
        self.assertEqual(len([d for d in self.lessons if d.code.startswith("MT6")]),10)

    def test_each_contains_teacher_pupil_activities_and_assessment(self):
        for d in self.lessons:
            with self.subTest(pdp=d.code):
                self.assertIn("Objektif",d.body)
                self.assertIn("Set induksi",d.body)
                for label in ("Aktiviti 1", "Aktiviti 2", "Aktiviti 3", "PBD", "Penutup", "BBM"):
                    self.assertIn(label,d.body)
                self.assertTrue(len(d.body)>650)
                self.assertNotIn("Pagar keselamatan", d.body)
                self.assertNotIn("Peraturan penerbitan", d.body)
                self.assertNotIn("###", d.body)
                self.assertNotIn("BELUM DILULUSKAN", d.body)
                self.assertIn(d.code,CANDIDATES)

    def test_candidates_not_approved_mapping_or_runtime_content(self):
        self.assertEqual(CANDIDATES["MT6-PDP-006"],("1.4.1","1.1.2","4–8"))
        self.assertEqual(CANDIDATES["MT6-PDP-079"],("8.1.1","7.2.1","191–196"))
        self.assertEqual(CANDIDATES["FIN-T6-02"],("TIADA","3.2.1","121–122"))
        self.assertTrue(all(d.source.startswith("rph_standalone/matematik/staging_draf_")
                            for d in self.lessons))

if __name__=="__main__":
    unittest.main()
