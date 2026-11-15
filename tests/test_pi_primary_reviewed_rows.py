"""Regression coverage for source-checked Jawi and tilawah RPH."""

import copy
import unittest

from web.pi_primary_reviewed_rows import apply_primary_reviewed_rows


def context(year, row, sequence, codes, texts):
    return {
        "year": f"Tahun {year}",
        "rpt_entry_id": row,
        "_quick_selected_rpt_row_v2388": {"sequence_no": sequence},
        "selected_sp_codes": codes,
        "grouped_sp_texts": texts,
    }


class PIReviewedRowsTests(unittest.TestCase):
    def test_repeated_web_and_telegram_standards_are_listed_once(self):
        first = "مڠنل دان مثبوت حروف۲ جاوي توڠݢل."
        second = "ملاكر دان ممبنتوق ڤلباݢاي چورق."
        joined = f"7.1.1 {first} 7.1.2 {second}"
        for source in (joined, f"{first} 7.1.2 {second}"):
            with self.subTest(source=source):
                state = context(1, 1166, 3, ["7.1.1", "7.1.2"], [source, joined])
                original = copy.deepcopy(state)
                rows = apply_primary_reviewed_rows(state, {})
                self.assertEqual(rows["STANDARD PEMBELAJARAN"], f"7.1.1 {first}\n7.1.2 {second}")
                self.assertIn("6 حرف", rows["PENTAKSIRAN"])
                self.assertIn("2 لاکرن", rows["PENTAKSIRAN"])
                self.assertEqual(state, original)

    def test_both_al_kafirun_ranges_are_corrected_in_objective_and_activity(self):
        for row, sequence, old, new in (
            (1387, 1, "3-1", "1 هيڠݢ 3"),
            (1391, 5, "5-4", "4 هيڠݢ 5"),
        ):
            with self.subTest(sequence=sequence):
                state = context(3, row, sequence, ["1.1.1"], ["1.1.1 ممباچ سورة الكافرون."])
                objective = f"ممباچ سورة الكافرون اية {old} دڠن بتول."
                rows = apply_primary_reviewed_rows(state, {"OBJEKTIF PEMBELAJARAN": objective})
                self.assertIn(new, rows["OBJEKTIF PEMBELAJARAN"])
                self.assertNotIn(old, rows["OBJEKTIF PEMBELAJARAN"])
                self.assertIn(new, rows["AKTIVITI UTAMA"])
                self.assertIn("تجويد", rows["PENTAKSIRAN"])
                rows = {"OBJEKTIF PEMBELAJARAN": objective.replace("الكافرون", "الناس")}
                before = rows.copy()
                self.assertEqual(apply_primary_reviewed_rows(state, rows), before)

    def test_prefix_lesson_preserves_jawi_orthography_and_assesses_reading(self):
        state = context(3, 1390, 4, ["7.1.1"], ["7.1.1 – ممباچ تيك س موده دان ريڠكس."])
        rows = apply_primary_reviewed_rows(state, {"OBJEKTIF PEMBELAJARAN": "ممباچ تيك س."})
        self.assertEqual(rows["STANDARD PEMBELAJARAN"], "7.1.1 ممباچ تيك س موده دان ريڠكس.")
        self.assertIn("ممباچ ڤتيقن", rows["AKTIVITI UTAMA"])
        self.assertNotIn("املاق", rows["AKTIVITI UTAMA"])

    def test_syllable_lesson_assesses_reading_and_building(self):
        source = "6.1.1 – ممباچ ڤركاتاءن. 6.1.2- ممبينا ڤركاتاءن."
        state = context(2, 1277, 3, ["6.1.1", "6.1.2"], [source, source])
        rows = apply_primary_reviewed_rows(state, {})
        self.assertEqual(rows["STANDARD PEMBELAJARAN"], "6.1.1 ممباچ ڤركاتاءن.\n6.1.2 ممبينا ڤركاتاءن.")
        self.assertIn("3 باچاءن", rows["PENTAKSIRAN"])
        self.assertIn("2 سوسونن", rows["PENTAKSIRAN"])

    def test_upper_primary_jawi_removes_repeated_codes_and_adds_individual_checks(self):
        first = "7.1.1 – ممباچ."
        second = "7.1.2- منوليس."
        combined = f"{first} {second}"
        for year, row, goal in ((4, 1538, "همزة"), (5, 1690, "صيحت"), (6, 1834, "تيکنولوݢي")):
            with self.subTest(year=year):
                state = context(year, row, 4, ["7.1.1", "7.1.2"], [combined, combined])
                rows = apply_primary_reviewed_rows(state, {})
                self.assertEqual(rows["STANDARD PEMBELAJARAN"], "7.1.1 ممباچ.\n7.1.2 منوليس.")
                self.assertIn(goal, rows["KRITERIA KEJAYAAN"])
                self.assertEqual(rows["AKTIVITI UTAMA"].count("اکتيۏيتي"), 3)
                self.assertIn("مڽمق" if year > 4 else "مريکود", rows["PENTAKSIRAN"])

    def test_another_lesson_is_out_of_scope(self):
        rows = {"OBJEKTIF PEMBELAJARAN": "ممباچ سورة الكافرون اية 3-1"}
        copy_before = rows.copy()
        state = context(3, 1391, 1, ["1.1.1"], ["1.1.1 ممباچ سورة الكافرون."])
        self.assertEqual(apply_primary_reviewed_rows(state, rows), copy_before)
