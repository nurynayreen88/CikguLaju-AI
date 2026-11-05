"""Guardrails for Pendidikan Muzik audit seeds: no accidental READY/release."""
import json
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1] / "staging" / "pendidikan_muzik"
COUNTS = {2: 20, 3: 22, 4: 19, 5: 20, 6: 18}
SECTIONS = {"set_induksi", "aktiviti_utama", "pengukuhan_penilaian", "penutup", "bahan"}


class PendidikanMuzikStagingQA(unittest.TestCase):
    def test_sp_coverage_and_no_live_flags(self):
        all_keys = set()
        for year, expected in COUNTS.items():
            item = json.loads((ROOT / f"y{year}_dskp_sp_rph_seeds.json").read_text(encoding="utf-8"))
            self.assertEqual(item["year"], year)
            self.assertTrue(item["not_for_live"])
            self.assertFalse(item["rpt_2026_crosswalk_complete"])
            self.assertFalse(item["rpt_2027_ready"])
            self.assertFalse(item["book_page_verified"])
            self.assertFalse(item["audio_track_verified"])
            standards = item["standards"]
            self.assertEqual(len(standards), expected)
            for entry in standards:
                key = (year, entry["sp"])
                self.assertNotIn(key, all_keys)
                all_keys.add(key)
                self.assertRegex(entry["sp"], r"^[1-5][.][1-9][.][0-9]{1,2}$")
                self.assertTrue(entry["ringkasan_sp"].strip())
                draft = entry["rph_seed"]
                self.assertTrue(SECTIONS <= set(draft))
                self.assertEqual(len(draft["aktiviti_utama"]), 2)
                self.assertIsNone(draft["rujukan_halaman_buku_teks"])
                self.assertIsNone(draft["rujukan_audio_track"])
                self.assertFalse(draft["validated_against_rpt"])
                self.assertFalse(draft["validated_against_textbook"])
                self.assertIn("DRAF", draft["status"])
        self.assertEqual(len(all_keys), 99)

    def test_year4_source_code_mismatches_are_preserved_and_flagged(self):
        data = json.loads((ROOT / "y4_dskp_sp_rph_seeds.json").read_text(encoding="utf-8"))
        flagged = {s["sp"]: s["sk_sumber"] for s in data["standards"] if s["flag_kod_sk_sp_tidak_sepadan"]}
        self.assertEqual(flagged, {"3.2.1": "3.1", "3.2.2": "3.1", "3.2.3": "3.1", "4.2.1": "4.1"})


if __name__ == "__main__":
    unittest.main()
