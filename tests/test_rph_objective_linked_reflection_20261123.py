"""Native KSSR source-aware reflection, no invented outcomes or edited subjects."""
import unittest
from types import SimpleNamespace

from web.rph_objective_linked_reflection_20261123 import (
    _focus, _language, objective_linked_reflection, install,
)

PI_OBJ = "موريد داڤت : ممباچ سورة البقرة أية 1-29 دڠن بتول دان برتجويد"
PI_STOCK = ("موريد داڤت منيرو، منونجوقکن اتاو مڽلسايکن توݢسن يڠ "
            "برکاءيتن دڠن فوکوس ڤدڤ سچارا بتول دڠن بيمبيڠن ݢورو.")
PI_GENERAL = ("____ / ____ موريد منچاپاي اوبجيکتيف. ____ / ____ "
              "موريد ممرلوکن بيمبيڠن لنجوتن.")
MALAY_CRITERION = "Murid mengenal pasti sekurang-kurangnya tiga isi penting dalam petikan."
EN_CRITERION = "Pupils answer at least 4 out of 5 reading questions correctly."


def pi_state(**extras):
    return {"task": "rph", "subject": "Pendidikan Islam",
            "rpt_entry_id": 1275, **extras}


def pi_rows():
    return {
        "STANDARD KANDUNGAN": "القرءان 1 جم",
        "STANDARD PEMBELAJARAN": "ختام / تسميع",
        "OBJEKTIF PEMBELAJARAN": PI_OBJ,
        "KRITERIA KEJAYAAN": PI_STOCK,
        "AKTIVITI UTAMA": "1. ممباچ اية سچارا تلقي دان مشافهة\n2. ممبتولكن باچاءن يڠ كورڠ فصيح\n3. ممبيمبيڠ راكن سباي\n4. ݢورو مريكوت ڤنچاڤاين موريد.",
        "REFLEKSI": PI_GENERAL,
        "PENUTUP": "موريد مروموسکن ڤمبلاجرن",
    }


class ObjectiveLinkedNativeReflectionTests(unittest.TestCase):
    def test_real_jawi_objective_not_generic_success_scaffold(self):
        original = pi_rows()
        updated = objective_linked_reflection(pi_state(), original)
        self.assertIsNot(updated, original)
        self.assertEqual(original["REFLEKSI"], PI_GENERAL)
        self.assertIn("سورة البقرة أية 1-29", updated["REFLEKSI"])
        self.assertIn("دڠن بتول دان برتجويد", updated["REFLEKSI"])
        self.assertNotIn("موريد داڤت منيرو", updated["REFLEKSI"])
        self.assertNotIn("(Auto", updated["REFLEKSI"])
        self.assertIn("____ / ____", updated["REFLEKSI"])
        for key in original.keys() - {"REFLEKSI"}:
            self.assertEqual(updated[key], original[key])
        self.assertIs(objective_linked_reflection(pi_state(), updated), updated)

    def test_malay_math_bm_sains_moral_and_music_use_actual_criterion(self):
        for subject in ("Bahasa Melayu", "Matematik", "Sains",
                        "Pendidikan Moral", "Pendidikan Muzik", "Sejarah",
                        "Pendidikan Seni Visual",
                        "Pendidikan Jasmani dan Pendidikan Kesihatan"):
            with self.subTest(subject=subject):
                rows = {"KRITERIA KEJAYAAN": MALAY_CRITERION,
                        "OBJEKTIF PEMBELAJARAN": "Murid membaca petikan.",
                        "REFLEKSI": "____ / ____ murid mencapai objektif."}
                result = objective_linked_reflection(
                    {"task": "rph", "subject": subject}, rows)
                self.assertIn("tiga isi penting", result["REFLEKSI"])
                self.assertNotIn("Murid membaca petikan", result["REFLEKSI"])
                self.assertEqual(result["KRITERIA KEJAYAAN"], MALAY_CRITERION)

    def test_english_uses_actual_success_criterion_not_bahasa_melayu(self):
        rows = {"KRITERIA KEJAYAAN": EN_CRITERION,
                "OBJEKTIF PEMBELAJARAN": "Pupils can read a short passage.",
                "REFLEKSI": "____ / ____ pupils achieved the lesson objectives."}
        result = objective_linked_reflection(
            {"task": "rph", "subject": "English"}, rows)
        self.assertIn("4 out of 5", result["REFLEKSI"])
        self.assertIn("pupils met the criterion", result["REFLEKSI"])
        self.assertNotIn("murid mencapai", result["REFLEKSI"])

    def test_manual_teacher_reflection_is_authoritative(self):
        original = pi_rows()
        manual = "Saya dapati murid perlu memperbaiki sebutan huruf."
        self.assertIs(objective_linked_reflection(
            pi_state(rph_teacher_reflection=manual), original), original)
        self.assertIs(objective_linked_reflection(
            pi_state(rph_reflection_mode="manual"), original), original)

    def test_preserve_already_specific_reflection_without_duplication(self):
        rows = pi_rows()
        rows["REFLEKSI"] = "25 murid dapat membaca Surah Al-Baqarah dengan tajwid."
        self.assertIs(objective_linked_reflection(pi_state(), rows), rows)

    def test_fail_closed_for_unsupported_and_protected_programmes(self):
        for extra in ({"subject": "Bahasa Arab"}, {"subject": "PPKI"},
                      {"subject": "Matematik", "programme": "DLP"},
                      {"subject": "Matematik", "school_type": "SJKC"},
                      {"subject": "Sains", "curriculum": "KP2027"},
                      {"subject": "Matematik", "stream": "SJKT"},
                      {"subject": "Matematik", "task": "worksheet"}):
            state = {"task": "rph", **extra}
            rows = {"OBJEKTIF PEMBELAJARAN": "Murid menjelaskan konsep pembelajaran.",
                    "KRITERIA KEJAYAAN": MALAY_CRITERION,
                    "REFLEKSI": "____ / ____ murid mencapai objektif."}
            self.assertIs(objective_linked_reflection(state, rows), rows)

    def test_fallback_to_objective_when_success_criterion_generic(self):
        rows = {"OBJEKTIF PEMBELAJARAN": "Murid boleh menyebut lima anggota badan.",
                "KRITERIA KEJAYAAN": "Murid menunjukkan penguasaan terhadap fokus pembelajaran.",
                "REFLEKSI": "____ / ____ murid mencapai objektif."}
        result = objective_linked_reflection(
            {"task": "rph", "subject": "Bahasa Melayu"}, rows)
        self.assertIn("lima anggota badan", result["REFLEKSI"])

    def test_no_source_or_long_ambiguous_source_is_not_paraphrased(self):
        s = {"task": "rph", "subject": "Matematik"}
        rows = {"REFLEKSI": "____ / ____ murid mencapai objektif.",
                "KRITERIA KEJAYAAN": "Murid menguasai fokus pembelajaran."}
        self.assertIs(objective_linked_reflection(s, rows), rows)
        rows["KRITERIA KEJAYAAN"] = ("Murid dapat menjelaskan satu kemahiran khusus "
                                     + "dengan pemerhatian dan penilaian. " * 8)
        self.assertIs(objective_linked_reflection(s, rows), rows)

    def test_double_install_retains_exact_text_and_manual_reflection(self):
        calls = []
        def native_rows(state, text):
            calls.append((state, text))
            return pi_rows()
        runtime = SimpleNamespace(_rph_rows=native_rows)
        self.assertTrue(install(runtime))
        self.assertTrue(install(runtime))
        state = pi_state()
        output = runtime._rph_rows(state, "ORIGINAL TEXT")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0], (state, "ORIGINAL TEXT"))
        self.assertIn("سورة البقرة", output["REFLEKSI"])
        self.assertEqual(output["AKTIVITI UTAMA"], pi_rows()["AKTIVITI UTAMA"])


if __name__ == "__main__":
    unittest.main()
