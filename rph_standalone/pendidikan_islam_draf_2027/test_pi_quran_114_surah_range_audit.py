"""Whole Quran surah length/cross-field regression, 696 RPH."""
import unittest
from pi_quran_114_surah_range_audit import audit, verse_catalog, parse


class PIQuranFullVerseRangeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data=audit()

    def test_quran_metadata_and_coverage(self):
        c=verse_catalog()
        self.assertEqual(len(c),116)  # 114 canonical plus two genuinely distinct aliases
        self.assertEqual(c["البقرة"],286)
        self.assertEqual(c["الكافرون"],6)
        self.assertEqual(c["العصر"],3)
        self.assertEqual(c["التكاثر"],8)
        self.assertEqual(c["القصص"],88)
        self.assertEqual(c["الحديد"],29)
        self.assertEqual(self.data["catalog_lesson_total"],696)
        self.assertEqual(self.data["unheld_drafts_examined"],690)
        self.assertGreaterEqual(self.data["verse_range_occurrences_evaluated"],750)

    def test_no_descending_or_out_of_surah_and_no_crossfield_mismatch(self):
        self.assertEqual(self.data["invalid_chapter_verse_ranges"],0)
        self.assertEqual(self.data["crossfield_surah_verse_mismatches"],0)
        self.assertEqual(self.data["RPH_corrected_after_rechecking"],
                         ["T3-L001","T3-L005","T5-L034","T6-L078"])
        self.assertFalse(self.data["original_rpt_overwritten"])
        self.assertEqual(self.data["teacher_ready"],0)
        self.assertEqual(self.data["release"],"NO_GO")

    def test_known_inverted_ranges_are_rejected(self):
        invalid=parse("ممباچ سورة الكافرون اية 3-1")
        self.assertEqual(len(invalid),1)
        self.assertGreater(invalid[0]["start"],invalid[0]["end"])
        self.assertEqual(parse("ممباچ سورة الكافرون اية 1-3")[0]["end"],3)

if __name__=="__main__":
    unittest.main()
