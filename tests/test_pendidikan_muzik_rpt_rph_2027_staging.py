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

    def test_week_slots_match_frozen_master_not_per_state_availability(self):
        """Master-index week ranges only. This does NOT validate school dates by state."""
        snapshot = json.loads((MUSIC / "rpt_rph_2027" / "KALENDAR_MINGGU_RPT_2027_INDUK_AUDIT_SNAPSHOT.json").read_text(encoding="utf-8"))
        self.assertFalse(snapshot["verification"]["release_authorization"])
        self.assertEqual(snapshot["verification"]["year2_to6_pdp"], 175)
        for group in ("A", "B"):
            self.assertEqual(len(snapshot["weeks"][group]), 44)
            self.assertEqual(set(snapshot["weeks"][group]), {f"M{i:02d}" for i in range(1, 45)})
            self.assertEqual(len(snapshot["school_break_week_slots"][group]), 4)
        self.assertEqual(snapshot["weeks"]["A"]["M10"]["start"], "2027-03-14")
        self.assertEqual(snapshot["weeks"]["B"]["M10"]["start"], "2027-03-15")
        self.assertEqual(snapshot["weeks"]["B"]["M20"]["start"], "2027-06-07")
        self.assertEqual(snapshot["weeks"]["B"]["M32"]["start"], "2027-09-06")

        import csv
        def short_date(iso):
            return iso[8:10] + "/" + iso[5:7]

        for year in range(2, 7):
            directory = MUSIC / "rpt_rph_2027" / f"year{year}"
            manifest = json.loads((directory / "pdp_manifest.json").read_text(encoding="utf-8"))
            with (directory / f"RPT_MUZIK_TAHUN_{year}_2027_DRAF.csv").open(encoding="utf-8", newline="") as fh:
                csv_rows = {row[0]: row for row in list(csv.reader(fh))[1:]}
            self.assertEqual(len(csv_rows), 35)
            for row in manifest["pdps"]:
                ident = row["pdp_id"]
                week_code = f"M{row['rpt2027_slot']['week']:02d}"
                for group, column in (("A", 2), ("B", 3)):
                    source = snapshot["weeks"][group][week_code]
                    expected = short_date(source["start"]) + "–" + short_date(source["end"])
                    self.assertEqual(row["rpt2027_slot"]["group" + group], expected)
                    self.assertEqual(csv_rows[ident][column], expected)

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

    def test_year4_crosswalk_sources_preserved_and_not_approved(self):
        manifest = json.loads((MUSIC / "rpt_rph_2027" / "year4" / "pdp_manifest.json").read_text(encoding="utf-8"))
        expected = {
            21: (["3.1.2", "3.1.3"], ["3.2.2", "3.2.3"]),
            24: (["3.1.1", "3.1.2", "3.1.3"], ["3.2.1", "3.2.2", "3.2.3"]),
        }
        for pdp, (source, printed) in expected.items():
            row = manifest["pdps"][pdp-1]
            self.assertEqual(row["sp"], source)
            self.assertEqual(row["dskp_source_printed_sp"], printed)
            self.assertEqual(row["textbook_printed_sp"], printed)
            self.assertFalse(row["dskp_crosswalk_approved"])
            self.assertEqual(row["dskp_crosswalk_review_level"], "SOURCE_VERIFIED_CODE_DIFFERENCE_UNRESOLVED")
            self.assertIn("drive.google.com", row["dskp_source_document_url"])
            doc = (MUSIC / "rpt_rph_2027" / "year4" / f"rph_pdp_{pdp:02d}.md").read_text(encoding="utf-8")
            self.assertIn("BELUM DILULUSKAN", doc)
            self.assertIn(", ".join(printed), doc)
        self.assertIn("G, A, B, C’", manifest["pdps"][20]["crosswalk_review_note"])

    def test_reinforcement_candidates_stay_nonofficial_and_no_fabricated_audio(self):
        """All eight non-book slots are specificity-reviewed but never count as book-verified."""
        total = 0
        for year in (2, 3, 4, 6):
            directory = MUSIC / "rpt_rph_2027" / f"year{year}"
            manifest = json.loads((directory / "pdp_manifest.json").read_text(encoding="utf-8"))
            for pdp in (34, 35):
                row = manifest["pdps"][pdp-1]
                self.assertEqual(row["pdp_kind"], "CADANGAN_PENGUKUHAN_BUKAN_PROJEK_RASMI")
                self.assertTrue(row["reinforcement_specificity_reviewed"])
                self.assertIsNone(row["page"])
                self.assertFalse(row.get("source_book_text_crosscheck", False))
                self.assertFalse(row["source_book_audio_file_verified"])
                self.assertTrue(row["validation_status"].startswith("DRAF_"))
                doc = (directory / f"rph_pdp_{pdp:02d}.md").read_text(encoding="utf-8")
                self.assertIn("BUKAN Projek Seni Muzik rasmi", doc)
                self.assertIn("BUKAN Projek Seni Muzik rasmi".upper(), doc.upper())
                self.assertIn("**Aktiviti 1", doc)
                self.assertIn("**Aktiviti 2", doc)
                self.assertIn("semakan teks buku", doc)
                total += 1
        self.assertEqual(total, 8)

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
            2: (33, set(range(1, 34))),
            3: (33, set(range(1, 34))),
            4: (27, set(range(1, 14)) | set(range(17, 31))),
            5: (35, set(range(1, 36))),
            6: (33, set(range(1, 34))),
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
        year2 = json.loads((MUSIC / "rpt_rph_2027" / "year2" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(year2["pdps"][10]["page"], "36-37")
        self.assertEqual(year2["pdps"][10]["source_rpt_original_page"], "32-33")
        self.assertEqual(year2["pdps"][21]["source_book_audio_numbers_printed"], "60–66 (berbeza rujukan RPT 57–59)")
        self.assertTrue(year2["pdps"][32].get("source_book_text_crosscheck", False))
        self.assertFalse(year2["pdps"][32].get("pending_book_page_crosscheck", False))
        self.assertIn("sompoton", (MUSIC / "rpt_rph_2027" / "year2" / "rph_pdp_33.md").read_text(encoding="utf-8"))
        self.assertTrue(all(year2["pdps"][i-1].get("source_book_project_evidence") for i in (12,13,26,27)))
        year3 = json.loads((MUSIC / "rpt_rph_2027" / "year3" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(year3["partial_textbook_crosscheck_count"], 33)
        self.assertEqual(year3["pdps"][5]["page"], "21")
        self.assertTrue(all(year3["pdps"][i-1]["source_book_project_evidence"] for i in (12,13,24,25,26)))
        self.assertFalse(any(year3["pdps"][i-1].get("source_book_text_crosscheck", False) for i in (34,35)))
        self.assertEqual(year3["pdps"][5]["source_rpt_original_page"], "20")
        self.assertEqual(year3["pdps"][9]["audio"], "39–40")
        self.assertEqual(year3["pdps"][9]["source_rpt_original_audio"], "36-38")
        self.assertEqual({r["pdp"] for r in year3["pdps"] if r.get("source_book_text_crosscheck")}, set(range(1, 34)))
        self.assertEqual(year3["pdps"][26]["audio"], "65")
        self.assertEqual(year3["pdps"][26]["source_rpt_original_audio"], "69-70")
        self.assertEqual(year3["pdps"][27]["page"], "81")
        self.assertEqual(year3["pdps"][27]["source_rpt_original_page"], "80-81")
        self.assertIn("12 detik", (MUSIC / "rpt_rph_2027" / "year3" / "rph_pdp_20.md").read_text(encoding="utf-8"))
        self.assertIn("tiga jenis ikon", (MUSIC / "rpt_rph_2027" / "year3" / "rph_pdp_32.md").read_text(encoding="utf-8"))
        self.assertIn("rock balada", (MUSIC / "rpt_rph_2027" / "year3" / "rph_pdp_33.md").read_text(encoding="utf-8"))
        self.assertTrue(all(r["source_book_audio_file_verified"] is False for r in year3["pdps"][3:11]))
        self.assertIn("tempo lambat", (MUSIC / "rpt_rph_2027" / "year3" / "rph_pdp_06.md").read_text(encoding="utf-8"))
        self.assertIn("Gigih Si Labah-labah", (MUSIC / "rpt_rph_2027" / "year3" / "rph_pdp_10.md").read_text(encoding="utf-8"))
        self.assertIn("Muzik Jaz", (MUSIC / "rpt_rph_2027" / "year3" / "rph_pdp_11.md").read_text(encoding="utf-8"))
        self.assertFalse(year3["textbook_verified"])
        year4 = json.loads((MUSIC / "rpt_rph_2027" / "year4" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(year4["partial_page_content_check_count"], 6)
        self.assertEqual(year4["partial_text_crosscheck_count"], 27)
        self.assertTrue(all(year4["pdps"][i-1].get("source_book_project_evidence") for i in (12,13,25,26,27)))
        self.assertEqual([year4["pdps"][i-1]["page"] for i in (12,13,25,26,27)], ["4-5","4-5","54-55","54-55","54-55"])
        self.assertFalse(year4["pdps"][33].get("source_book_text_crosscheck", False))
        self.assertFalse(year4["pdps"][34].get("source_book_text_crosscheck", False))
        y5 = json.loads((MUSIC / "rpt_rph_2027" / "year5" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(y5["partial_textbook_crosscheck_count"], 35)
        self.assertIn("Da Dum", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_01.md").read_text(encoding="utf-8"))
        self.assertIn("Permainan Teroka Bunyi", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_02.md").read_text(encoding="utf-8"))
        self.assertIn("meter 3/4", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_06.md").read_text(encoding="utf-8"))
        self.assertIn("Lightly Row", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_08.md").read_text(encoding="utf-8"))
        self.assertIn("Dua Kekal Dua Mengembara", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_11.md").read_text(encoding="utf-8"))
        self.assertFalse(any(r.get("source_book_audio_file_verified") for r in y5["pdps"][:11]))
        self.assertIn("melodi kaunter", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_19.md").read_text(encoding="utf-8"))
        self.assertIn("Siapa yang Kena", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_22.md").read_text(encoding="utf-8"))
        self.assertIn("Lompat Luncur", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_25.md").read_text(encoding="utf-8"))
        self.assertIn("Cipta Melodi Indah", (MUSIC / "rpt_rph_2027" / "year5" / "rph_pdp_26.md").read_text(encoding="utf-8"))
        self.assertTrue(all(r.get("source_book_audio_file_verified") is False for r in y5["pdps"]))
        self.assertEqual(y5["pdps"][30]["source_rpt_original_page"], "80-83")
        self.assertEqual(y5["pdps"][31]["source_rpt_original_page"], "80-83")
        self.assertEqual(y5["pdps"][30]["page"], "80-81")
        self.assertEqual(y5["pdps"][31]["page"], "82-83")
        y6 = json.loads((MUSIC / "rpt_rph_2027" / "year6" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(y6["partial_textbook_crosscheck_count"], 33)
        self.assertEqual(y6["pdps"][4]["page"], "14-17")
        self.assertEqual(y6["pdps"][4]["source_rpt_original_page"], "14-15")
        self.assertIn("crescendo", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_01.md").read_text(encoding="utf-8"))
        self.assertIn("32 detik", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_02.md").read_text(encoding="utf-8"))
        self.assertIn("EMI Music Publishing", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_06.md").read_text(encoding="utf-8"))
        self.assertIn("kontur melodi", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_10.md").read_text(encoding="utf-8"))
        self.assertIn("minim bertitik", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_18.md").read_text(encoding="utf-8"))
        self.assertIn("fermata", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_19.md").read_text(encoding="utf-8"))
        self.assertIn("combo-mat", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_23.md").read_text(encoding="utf-8"))
        self.assertIn("Kutub Utara", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_24.md").read_text(encoding="utf-8"))
        self.assertIn("melodi kaunter", (MUSIC / "rpt_rph_2027" / "year6" / "rph_pdp_29.md").read_text(encoding="utf-8"))
        self.assertTrue(all(y6["pdps"][i-1]["project_book_evidence"] for i in (12,13,26,27)))
        self.assertEqual([y6["pdps"][i-1]["page"] for i in (12,13,26,27)], ["44-45","44-45","88-89","88-89"])
        self.assertFalse(y6["pdps"][33].get("source_book_text_crosscheck", False))
        self.assertFalse(y6["pdps"][34].get("source_book_text_crosscheck", False))
        self.assertTrue(all(r.get("source_book_audio_file_verified") is False for r in y6["pdps"] if r.get("source_book_text_crosscheck")))
        self.assertFalse(any(x["source_book_audio_file_verified"] for x in y6["pdps"][:10]))
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
