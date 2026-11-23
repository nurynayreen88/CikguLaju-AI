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
                existing = ("____ / ____ murid mencapai objektif. "
                            "____ / ____ murid belum mencapai objektif dan "
                            "memerlukan sokongan pemulihan, semakan tambahan "
                            "serta bimbingan khusus berdasarkan pencapaian akhir PdP.")
                rows = {"KRITERIA KEJAYAAN": MALAY_CRITERION,
                        "OBJEKTIF PEMBELAJARAN": "Murid membaca petikan.",
                        "REFLEKSI": ("____ / ____ murid mencapai objektif."
                                    if subject == "Bahasa Melayu" else existing)}
                result = objective_linked_reflection(
                    {"task": "rph", "subject": subject}, rows)
                self.assertIn("tiga isi penting", result["REFLEKSI"])
                self.assertNotIn("Murid membaca petikan", result["REFLEKSI"])
                self.assertEqual(result["KRITERIA KEJAYAAN"], MALAY_CRITERION)

    def test_real_bm_generic_targets_fall_back_to_verified_sp_and_topic(self):
        rows = {
            "KRITERIA KEJAYAAN": (
                "Murid membaca bahan sasaran mengikut fokus kemahiran dan "
                "menunjukkan kefahaman melalui respons yang tepat."),
            "OBJEKTIF PEMBELAJARAN": (
                "Pada akhir pembelajaran, murid dapat menunjukkan pengetahuan "
                "atau kemahiran berdasarkan Standard Pembelajaran 2.1.1 "
                "melalui tugasan berpandu dan individu."),
            "STANDARD PEMBELAJARAN": (
                "2.1.1 Membaca dengan sebutan yang betul dan intonasi yang sesuai; "
                "(i) perkataan (ii) ayat (iii) perenggan (iv) petikan"),
            "TAJUK": "Hari Minggu dengan Keluarga — Membeli Bahan Kek",
            "REFLEKSI": "____ / ____ murid mencapai objektif.",
        }
        result = objective_linked_reflection(
            {"task": "rph", "subject": "Bahasa Melayu"}, rows)
        self.assertIn("Membaca dengan sebutan yang betul", result["REFLEKSI"])
        self.assertIn("Membeli Bahan Kek", result["REFLEKSI"])
        self.assertNotIn("bahan sasaran", result["REFLEKSI"])
        self.assertNotIn("fokus kemahiran", result["REFLEKSI"])
        self.assertEqual(result["STANDARD PEMBELAJARAN"], rows["STANDARD PEMBELAJARAN"])
        self.assertEqual(result["OBJEKTIF PEMBELAJARAN"], rows["OBJEKTIF PEMBELAJARAN"])

    def test_english_uses_actual_success_criterion_not_bahasa_melayu(self):
        rows = {"KRITERIA KEJAYAAN": EN_CRITERION,
                "OBJEKTIF PEMBELAJARAN": "Pupils can read a short passage.",
                "REFLEKSI": ("____ / ____ pupils achieved the lesson objectives. "
                             "____ / ____ pupils require further support and "
                             "targeted reinforcement after this lesson.")}
        result = objective_linked_reflection(
            {"task": "rph", "subject": "English"}, rows)
        self.assertIn("4 out of 5", result["REFLEKSI"])
        self.assertIn("pupils met the criterion", result["REFLEKSI"])
        self.assertNotIn("murid mencapai", result["REFLEKSI"])

    def test_sains_verified_years_2_4_5_6_use_short_source_specific_reflections(self):
        """Four actual Sains source criteria from verified Year 2-6 samples."""
        source_targets = {
            2: "menyatakan cara haiwan membiak",
            4: ("mengenal pasti beban, fulkrum dan daya pada tuas "
                "dengan menjalankan aktiviti"),
            5: "memerihalkan fungsi rangka utama manusia",
            6: "menyatakan maksud teknologi dan kepentingannya",
        }
        original = (
            "________ / ________ murid mencapai objektif. ________ murid "
            "belum mencapai objektif dan akan diberi tindakan susulan/pemulihan."
        )
        for year, target in source_targets.items():
            with self.subTest(year=year):
                criterion = (
                    "Murid dapat " + target +
                    " dengan betul pada sekurang-kurangnya 4 daripada 5 "
                    "item atau situasi yang diberi."
                )
                rows = {
                    "KRITERIA KEJAYAAN": criterion,
                    "OBJEKTIF PEMBELAJARAN": (
                        "Pada akhir PdP, murid dapat " + target +
                        " dengan tepat berdasarkan aktiviti dan bukti yang diberikan."
                    ),
                    "AKTIVITI UTAMA": "Aktiviti 1 – Siasatan\nGuru membimbing.",
                    "REFLEKSI": original,
                }
                state = {"task": "rph", "subject": "Sains"}
                result = objective_linked_reflection(state, rows)
                self.assertIsNot(result, rows)
                self.assertEqual(
                    result["REFLEKSI"],
                    "____ / ____ murid " + target + " (4/5 item). Baki dibimbing."
                )
                self.assertLessEqual(len(result["REFLEKSI"]), len(original))
                self.assertNotIn("Auto", result["REFLEKSI"])
                self.assertNotIn("Manual", result["REFLEKSI"])
                for key in rows.keys() - {"REFLEKSI"}:
                    self.assertEqual(result[key], rows[key])
                meaningful = dict(rows)
        meaningful["KRITERIA KEJAYAAN"] = (
            "Murid dapat menyatakan cara haiwan membiak dengan betul pada "
            "sekurang-kurangnya 4 daripada 5 item atau situasi yang diberi."
        )
        self.assertIs(objective_linked_reflection(
            {**state, "rph_reflection_mode": "manual"}, meaningful), meaningful)
        self.assertIs(objective_linked_reflection(
            {**state, "rph_teacher_reflection": "Saya pilih catatan sendiri."},
            meaningful), meaningful)
        short = dict(meaningful)
        short["REFLEKSI"] = "Murid mencapai objektif."
        self.assertIs(objective_linked_reflection(state, short), short)

    def test_other_subjects_cannot_add_page_pressure_from_short_reflection(self):
        for subject in ("Sains", "Matematik", "English", "Sejarah",
                        "Pendidikan Moral", "Pendidikan Muzik"):
            original = {"KRITERIA KEJAYAAN": MALAY_CRITERION,
                        "OBJEKTIF PEMBELAJARAN": "Murid membaca petikan.",
                        "REFLEKSI": "____ / ____ murid mencapai objektif."}
            if subject == "English":
                original = {"KRITERIA KEJAYAAN": EN_CRITERION,
                            "OBJEKTIF PEMBELAJARAN": "Pupils read a short passage.",
                            "REFLEKSI": "____ / ____ pupils achieved the lesson objectives."}
            self.assertIs(objective_linked_reflection(
                {"task": "rph", "subject": subject}, original), original)

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
