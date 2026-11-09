"""Non-destructive Mathematics duplicate-SK regression coverage."""
import unittest
from types import SimpleNamespace

from web.math_rph_sk_display_fix_20261110 import (
    clean_duplicate_sk_prefixes, install,
)


class MathSKDisplayTests(unittest.TestCase):
    def test_exact_adjacent_duplicate_is_removed(self):
        samples = {
            "4.4 4.4 Darab wang": "4.4 Darab wang",
            "4.4 4.4": "4.4",
            "4.4 4.4 Darab wang; 4.5 4.5 Bahagi wang":
                "4.4 Darab wang; 4.5 Bahagi wang",
            " 4.4 4.4 Darab wang; 4.5 4.5 Bahagi wang":
                " 4.4 Darab wang; 4.5 Bahagi wang",
        }
        for source, expected in samples.items():
            with self.subTest(source=source):
                self.assertEqual(clean_duplicate_sk_prefixes(source), expected)
                self.assertEqual(clean_duplicate_sk_prefixes(expected), expected)

    def test_different_codes_and_real_curriculum_numbers_remain(self):
        for source in (
            "4.4 Darab wang", "4.4 4.4.1 Darab wang",
            "4.4 4.5 Darab dan bahagi wang",
            "4.4 Darab 4.4 kg bahan", "4.4.1 4.4.1 Bukan SK",
            "4.4 Darab wang; 4.5 Bahagi wang",
        ):
            with self.subTest(source=source):
                self.assertEqual(clean_duplicate_sk_prefixes(source), source)
        self.assertIsNone(clean_duplicate_sk_prefixes(None))

    def test_installed_runtime_preserves_all_fields_and_source_state(self):
        state = {
            "subject": "Matematik", "year": "Tahun 3",
            "sk_code": "4.4", "sk_text": "4.4 Darab wang",
            "sp_code": "4.4.1", "sp_text": "Mendarab nilai wang",
            "rph_class": "4 Ikhlas", "rph_time": "08:00-09:00",
        }
        source = {
            "STANDARD KANDUNGAN": "4.4 4.4 Darab wang",
            "STANDARD PEMBELAJARAN": "4.4.1 Mendarab nilai wang",
            "OBJEKTIF PEMBELAJARAN": "Objektif asal (masih perlu semakan guru)",
            "AKTIVITI UTAMA": "Aktiviti 1 (20 minit)\nAktiviti 2 (30 minit)",
            "MASA": "08:00-09:00",
            "KELAS": "4 Ikhlas",
        }
        runtime = SimpleNamespace(_rph_rows=lambda s, t: source)
        self.assertTrue(install(runtime))
        self.assertFalse(install(runtime))
        result = runtime._rph_rows(state, "RPH original")
        self.assertEqual(result["STANDARD KANDUNGAN"], "4.4 Darab wang")
        for key in source.keys() - {"STANDARD KANDUNGAN"}:
            self.assertEqual(result[key], source[key])
        self.assertEqual(source["STANDARD KANDUNGAN"], "4.4 4.4 Darab wang")
        self.assertEqual(state["sk_text"], "4.4 Darab wang")
        self.assertEqual(state["sp_code"], "4.4.1")

    def test_other_subjects_are_byte_for_byte_unchanged(self):
        original = {
            "STANDARD KANDUNGAN": "4.4 4.4 Darab wang",
            "STANDARD PEMBELAJARAN": "4.4.1",
        }
        runtime = SimpleNamespace(_rph_rows=lambda s, t: original)
        install(runtime)
        for subject in ("Sains", "Pendidikan Islam", "Bahasa Melayu",
                        "English", "Bahasa Arab"):
            result = runtime._rph_rows({"subject": subject}, "RPH")
            self.assertIs(result, original)

    def test_unrelated_math_text_remains_unmodified(self):
        original = {"STANDARD KANDUNGAN": "4.4 4.5 Darab dan bahagi wang"}
        runtime = SimpleNamespace(_rph_rows=lambda s, t: original)
        install(runtime)
        self.assertIs(runtime._rph_rows({"subject": "Matematik"}, "RPH"), original)


if __name__ == "__main__":
    unittest.main()
