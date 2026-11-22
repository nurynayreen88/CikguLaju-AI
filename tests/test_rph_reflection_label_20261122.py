"""UI reflection mode must not be printed as an RPH section label."""
import unittest

from web.rph_teacher_reflection import install, normalize_reflection_row_labels


class ReflectionDisplayLabelTests(unittest.TestCase):
    def test_ui_suffix_is_removed_without_changing_reflection_text(self):
        source = {
            "REFLEKSI (Auto / Manual)": "PdP dilaksanakan mengikut perancangan.",
            "AKTIVITI UTAMA": "Murid memadankan kad.",
        }
        result = normalize_reflection_row_labels(source)
        self.assertEqual(result["REFLEKSI"], source["REFLEKSI (Auto / Manual)"])
        self.assertNotIn("REFLEKSI (Auto / Manual)", result)
        self.assertEqual(result["AKTIVITI UTAMA"], source["AKTIVITI UTAMA"])
        self.assertIn("REFLEKSI (Auto / Manual)", source)

    def test_existing_reflection_and_other_rows_remain_intact(self):
        rows = {"REFLEKSI": "Refleksi asal.", "PENUTUP": "Rumusan."}
        self.assertIs(normalize_reflection_row_labels(rows), rows)
        mixed = {**rows, "Refleksi (Automatik / Manual)": "Teks berulang."}
        result = normalize_reflection_row_labels(mixed)
        self.assertEqual(result, rows)

    def test_installed_wrapper_uses_canonical_key_for_manual_and_auto(self):
        class Runtime:
            def _rph_rows(self, state):
                return {"Refleksi (Auto / Manual)": "Teks auto.", "TAJUK": "Asal"}
        runtime = Runtime()
        self.assertTrue(install(runtime))
        self.assertEqual(runtime._rph_rows({})["REFLEKSI"], "Teks auto.")
        self.assertEqual(runtime._rph_rows({"rph_teacher_reflection": "Teks manual."})["REFLEKSI"], "Teks manual.")
        self.assertEqual(runtime._rph_rows({})["TAJUK"], "Asal")


if __name__ == "__main__":
    unittest.main()
