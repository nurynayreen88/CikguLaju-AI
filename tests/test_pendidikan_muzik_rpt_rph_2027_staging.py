"""Guardrails for Pendidikan Muzik RPT/RPH 2027 staging."""
import csv
import json
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
MUSIC = ROOT / "staging" / "pendidikan_muzik"
YEAR_COUNTS = {2: 35, 3: 35, 4: 35, 5: 35, 6: 35}
REQUIRED = (
    "**Set Induksi", "**Set induksi", "**Aktiviti 1", "**Aktiviti 2",
    "**Penutup", "**Bahan", "**Status", "**Objektif",
)


class MusicRPTAndRPHStagingQA(unittest.TestCase):
    def test_pdp_identity_rpt_rph_coverage(self):
        all_keys = set()
        for year, expected in YEAR_COUNTS.items():
            directory = MUSIC / "rpt_rph_2027" / f"year{year}"
            manifest = json.loads((directory / "pdp_manifest.json").read_text(encoding="utf-8"))
            self.assertEqual(manifest["year"], year)
            self.assertEqual(manifest["academic_year"], 2027)
            self.assertIn("DRAF", manifest["status"])
            self.assertFalse(manifest["textbook_verified"])
            self.assertFalse(manifest["audio_verified"])
            self.assertFalse(manifest["rph_word_pdf_verified"])

            pdps = manifest["pdps"]
            self.assertEqual(len(pdps), expected)
            catalogue = json.loads((MUSIC / f"y{year}_dskp_sp_rph_seeds.json").read_text(encoding="utf-8"))
            known_sp = {row["sp"] for row in catalogue["standards"]}
            paths = sorted(directory.glob("rph_pdp_??.md"))
            self.assertEqual(len(paths), expected)
            for i, row in enumerate(pdps, start=1):
                self.assertEqual(row["pdp"], i)
                self.assertEqual(row["pdp_id"], f"MZ-Y{year}-{i:02d}")
                self.assertNotIn(row["pdp_id"], all_keys)
                all_keys.add(row["pdp_id"])
                self.assertTrue(row["unit"].strip())
                self.assertTrue(row["sp"])
                self.assertRegex(row["rpt2027_slot"]["groupA"], r"^\d{2}/\d{2}")
                self.assertRegex(row["rpt2027_slot"]["groupB"], r"^\d{2}/\d{2}")
                md = (directory / f"rph_pdp_{i:02d}.md").read_text(encoding="utf-8")
                self.assertIn(" ".join(row["unit"].split()), " ".join(md.split()))
                self.assertIn(f"PdP {i:02d}", md)
                self.assertIn("DRAF STAGING", md)
                for field in REQUIRED:
                    if field.startswith("**Set"):
                        continue
                    self.assertIn(field, md)
                self.assertTrue("**Set Induksi" in md or "**Set induksi" in md)
                self.assertEqual(md.count("**Aktiviti 1"), 1)
                self.assertEqual(md.count("**Aktiviti 2"), 1)
                for sp in row["sp"]:
                    self.assertRegex(sp, r"^[1-5][.][1-9][.]\d{1,2}$")
                missing = set(row["sp"]) - known_sp
                if missing:
                    self.assertEqual(year, 4, "Unknown SP outside known Year 4 source conflict")
                    self.assertTrue(row.get("flags") or "AMARAN KOD" in md)
            rpt_csv = directory / f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv"
            with rpt_csv.open(encoding="utf-8-sig", newline="") as f:
                rows = list(csv.reader(f))
            self.assertEqual(len(rows), expected + 1)
            rpt_md = (directory / f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.md").read_text(encoding="utf-8")
            self.assertIn("KUMPULAN A & B", rpt_md.upper())
            self.assertIn("DRAF", rpt_md)
        self.assertEqual(len(all_keys), 175)

    def test_conflicting_year_4_codes_not_automatically_normalized(self):
        directory = MUSIC / "rpt_rph_2027" / "year4"
        manifest = json.loads((directory / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(any(row.get("flags") for row in manifest["pdps"]))
        self.assertEqual(
            [row["pdp"] for row in manifest["pdps"] if row.get("source_book_content_page_checked")],
            [14, 15, 16, 31, 32, 33],
        )
        self.assertEqual({row["pdp"]: row["page"] for row in manifest["pdps"] if row.get("source_book_content_page_checked")},
                         {14: "50-51", 15: "52-53", 16: "52-53", 31: "100-101", 32: "102-103", 33: "102-103"})
        self.assertTrue(all("4.1.1" in row["sp_rpt_source"] for row in manifest["pdps"] if row.get("source_book_content_page_checked")))
        self.assertTrue(all("4.1.1" not in row["sp"] for row in manifest["pdps"] if row.get("source_book_content_page_checked")))
        self.assertTrue(all(not row["source_book_audio_file_verified"] for row in manifest["pdps"] if row.get("source_book_content_page_checked")))
        self.assertTrue(any("3.1.1" in row["sp"] for row in manifest["pdps"]))
        sources = json.loads((MUSIC / "y4_dskp_sp_rph_seeds.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {x["sp"] for x in sources["standards"] if x["flag_kod_sk_sp_tidak_sepadan"]},
            {"3.2.1", "3.2.2", "3.2.3", "4.2.1"},
        )

    def test_only_two_official_music_projects_each_year(self):
        for year in YEAR_COUNTS:
            directory = MUSIC / "rpt_rph_2027" / f"year{year}"
            manifest = json.loads((directory / "pdp_manifest.json").read_text(encoding="utf-8"))
            project_names = {row["unit"].split(" — ")[0] for row in manifest["pdps"] if row["unit"].startswith("Projek Seni Muzik")}
            self.assertEqual(project_names, {"Projek Seni Muzik 1", "Projek Seni Muzik 2"})
            self.assertFalse(any("Projek Seni Muzik 3" in row["unit"] for row in manifest["pdps"]))
            if year != 5:
                self.assertEqual(manifest["deprecated_project3_reclassified_count"], 2)
                extra = manifest["pdps"][-2:]
                self.assertTrue(all(row["pdp_kind"] == "CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI" for row in extra))
                self.assertTrue(all("Projek Seni Muzik 3" in row["source_rpt_original_unit"] for row in extra))
                self.assertTrue(all(row["validation_status"].startswith("DRAF") for row in extra))

    def test_textbook_crosscheck_is_partial_and_audio_is_unverified(self):
        expected = {
            4: (22, {1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 17, 18, 19, 20, 21, 22, 23, 24, 28, 29, 30}),
            5: (15, {12, 13, 14, 15, 16, 17, 27, 28, 29, 30, 31, 32, 33, 34, 35}),
            6: (7, {11, 14, 15, 30, 31, 32, 33}),
        }
        for year, (count, pdp_numbers) in expected.items():
            manifest = json.loads((MUSIC / "rpt_rph_2027" / f"year{year}" / "pdp_manifest.json").read_text(encoding="utf-8"))
            actual = {r["pdp"] for r in manifest["pdps"] if r.get("source_book_text_crosscheck")}
            self.assertEqual(actual, pdp_numbers)
            self.assertEqual(manifest["partial_textbook_crosscheck_count"] if year != 4 else manifest["partial_text_crosscheck_count"], count)
            self.assertFalse(manifest["textbook_verified"])
            self.assertFalse(manifest["audio_verified"])
            self.assertFalse(manifest["rph_word_pdf_verified"])
            self.assertTrue(all(r.get("source_book_audio_file_verified") is False for r in manifest["pdps"] if r.get("source_book_text_crosscheck")))
        year4 = json.loads((MUSIC / "rpt_rph_2027" / "year4" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(year4["partial_page_content_check_count"], 6)
        y5 = json.loads((MUSIC / "rpt_rph_2027" / "year5" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(y5["pdps"][30]["source_rpt_original_page"], "80-83")
        self.assertEqual(y5["pdps"][31]["source_rpt_original_page"], "80-83")
        self.assertEqual(y5["pdps"][30]["page"], "80-81")
        self.assertEqual(y5["pdps"][31]["page"], "82-83")
        y6 = json.loads((MUSIC / "rpt_rph_2027" / "year6" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(y6["pdps"][10]["dskp_classical_years"], "1750-1830")
        self.assertEqual(y6["pdps"][10]["textbook_classical_years"], "1750-1850")
        self.assertIn("Classical", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_11.md").read_text(encoding="utf-8"))

    def test_year_5_6_risks_remain_visible(self):
        y5 = json.loads((MUSIC / "rpt_rph_2027" / "year5" / "pdp_manifest.json").read_text(encoding="utf-8"))
        y6 = json.loads((MUSIC / "rpt_rph_2027" / "year6" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(y5["source_rpt_2026_crosswalk_checked"])
        self.assertEqual(y5["project_count_dskp"], 2)
        self.assertEqual([r["pdp"] for r in y5["pdps"] if r["unit"].startswith("Projek Seni Muzik")], [15, 16, 34, 35])
        self.assertFalse(any("Projek Seni Muzik 3" in r["unit"] for r in y5["pdps"]))
        self.assertEqual([(r["pdp"], r["page"]) for r in y5["pdps"] if r["unit"] == "ADIWIRA"], [(27, "70-71"), (28, "72-73"), (29, "74-77")])
        self.assertEqual([r["pdp"] for r in y5["pdps"] if r["unit"] == "RAJA DI LAUTAN"], [13, 14, 17])
        self.assertFalse(y5["textbook_verified"])
        self.assertFalse(y5["audio_verified"])
        self.assertFalse(y5["rph_word_pdf_verified"])
        self.assertTrue(any("Baroque" in " ".join(r.get("flags", [])) for r in y6["pdps"]))
        self.assertTrue(any("Classical" in " ".join(r.get("flags", [])) for r in y6["pdps"]))


if __name__ == "__main__":
    unittest.main()
