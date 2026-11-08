"""Static guards for physical A4 DOCX/PDF audit; no runtime publication."""
import unittest
from pi_word_pdf_print_audit import collect_records, rtl_preferred, display_bidi_safe, LABELS


class PIPhysicalPrintAuditTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.records = collect_records()

    def test_all_696_including_six_held_and_three_critical_hold(self):
        self.assertEqual(len(self.records), 696)
        counts = {}
        for row, status in self.records:
            counts[status] = counts.get(status, 0) + 1
        self.assertEqual(counts, {
            "HELD_NO_CONTENT": 6,
            "CRITICAL_SOURCE_HOLD": 3,
            "RENDER_PREVIEW_ONLY": 687,
        })
        self.assertEqual(
            [r["id"] for r, s in self.records if s == "CRITICAL_SOURCE_HOLD"],
            ["T4-L083", "T6-L137", "T6-L141"],
        )

    def test_diagnostic_never_changes_source_and_always_labels_draft(self):
        self.assertEqual(len(LABELS), 8)
        self.assertEqual(set(k for k, _ in LABELS), {
            "sk", "sp", "objektif", "set_induksi", "aktiviti_utama",
            "pentaksiran", "penutup", "bahan",
        })
        for row, status in self.records:
            self.assertIs(row["verified_ready"], False)
            if status == "RENDER_PREVIEW_ONLY":
                self.assertIn("DRAF", row["teacher_notice"])
                for key, _ in LABELS:
                    self.assertTrue(row["fields"][key].strip())
            else:
                self.assertNotEqual(status, "PUBLISHED")

    def test_right_to_left_detection_is_not_jawi_transliteration(self):
        jawi = "موريد ممباچ ڤتيقن دڠن بتول"
        self.assertTrue(rtl_preferred(jawi))
        self.assertFalse(rtl_preferred("Murid mengulang bacaan."))
        self.assertTrue(rtl_preferred("1. ݢورو ممبيمبيڠ موريد."))
        self.assertFalse(rtl_preferred("DRAF — Test Document"))


    def test_print_only_quran_ranges_keep_visual_left_to_right_order(self):
        # Word/LibreOffice in Jawi RTL paragraphs reverses bare 1-3 to 3-1.
        # The source JSON remains pure text; invisible U+200E is print-only.
        sample="موريد ممباچ سورة الكافرون اية 1-3 دڠن بتول."
        display=display_bidi_safe(sample)
        self.assertEqual(display.count("\u200e"),2)
        self.assertIn("\u200e1-3\u200e",display)
        self.assertEqual(display.replace("\u200e",""),sample)
        self.assertEqual(display_bidi_safe("Murid membaca ayat 1-3."),"Murid membaca ayat 1-3.")
        self.assertIn("\u200e53-75\u200e", display_bidi_safe("سورة الأنفال 53-75 دڠن بتول"))
        self.assertIn("\u200e2 - 3\u200e",display_bidi_safe("سورة اية 2 - 3 دڠن بتول"))



if __name__ == "__main__":
    unittest.main()
