"""Regression checks for PSV 2027 draft source order and Year 5 RPT objective alignment.

Read-only: this suite never modifies application data or production assets.
Run with: python -m unittest tests.test_psv_rpt_rph_source_order
"""
import csv
import json
import re
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PSV = ROOT / "rpt_2027" / "psv"


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def normalize_title(value):
    """Ignore punctuation and case differences, not meaningful word differences."""
    return " ".join(re.findall(r"\w+", value.casefold()))


class PSVSourceOrderTests(unittest.TestCase):
    def test_2027_unit_order_matches_2026_crosswalk(self):
        for year in range(2, 7):
            with self.subTest(year=year):
                expected = read_csv(PSV / f"crosswalk_2026_tahun{year}_VERIFIED_SOURCE.csv")
                actual = read_csv(PSV / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv")
                self.assertEqual(len(expected), 10)
                self.assertEqual(len(actual), 42)
                number_column = "Unit 2026" if year == 6 else "Unit"
                name_column = "Tajuk unit" if year == 6 else "Tajuk karya cadangan"
                seen = set()
                ordered = []
                for row in actual:
                    number = row[number_column].strip()
                    if not number.isdigit() or number in seen:
                        continue
                    seen.add(number)
                    ordered.append((int(number), normalize_title(row[name_column])))
                target = [(int(row["Unit RPT 2026"]), normalize_title(row["Nama unit"])) for row in expected]
                self.assertEqual(ordered, target)

    def test_year5_rpt_objective_and_evidence_match_rph(self):
        rpt = read_csv(PSV / "RPT_PSV_Tahun_5_2027_DRAF.csv")
        self.assertEqual(len(rpt), 42)
        for row in rpt:
            number = row["PdP"]
            with self.subTest(pdp=number):
                source = ROOT / row["Fail RPH"]
                text = source.read_text(encoding="utf-8")
                section = re.search(
                    r"(?ms)^## Objektif dan kriteria kejayaan\s*\n(.*?)\n## Langkah PdP",
                    text,
                )
                self.assertIsNotNone(section, str(source))
                match = re.fullmatch(r"(Murid dapat .*?)\s+(?:Evidens|Kriteria kejayaan):\s+(.*)", " ".join(section.group(1).split()))
                self.assertIsNotNone(match, str(source))
                objective = match.group(1).strip().rstrip(".")
                evidence = match.group(2).strip().rstrip(".")
                self.assertEqual(row["Objektif"], objective)
                self.assertEqual(row["Evidens PBD"], evidence)
                self.assertGreater(len(objective), 55)
                self.assertEqual(row["Status"], "DRAF_SEMAK")


    def test_year6_pdp_post_exhibition_standard(self):
        rows = read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")
        by_pdp = {row["PdP"]: row for row in rows}
        for pdp in ("026", "042"):
            with self.subTest(pdp=pdp):
                self.assertEqual(by_pdp[pdp]["SK"], "5.1")
                self.assertEqual(by_pdp[pdp]["SP"], "5.1.5")
                rph = (ROOT / by_pdp[pdp]["RPH"]).read_text(encoding="utf-8")
                self.assertIn("**SP:** 5.1.5", rph)
                self.assertNotIn("5.1.5 bukan kod Tahun 6", rph)

    def test_year6_unit1_activity_matches_textbook_pages(self):
        rows = read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")
        by_pdp = {row["PdP"]: row for row in rows}
        cases = {
            "002": ("Alat Tulis Saya", "ms 10–11", "garisan selari", "dua lakaran berlabel"),
            "003": ("Tingkap Damai", "ms 12–13", "tetingkap fokus", "tiga bahagian ruang"),
            "004": ("Dunia Gemilang", "ms 14–15", "arca tiga dimensi", "tiga ciri berlabel"),
            "005": ("Bersatu Teguh Bercerai Roboh", "ms 16–17", "tanggam", "dua percubaan susunan"),
            "006": ("Kotak Kejutan", "ms 18–19", "templat bentangan", "dua catatan bentuk/lipatan"),
            "007": ("Realiti Alam", "ms 20–21", "ruang ilusi", "tiga label tepat"),
            "008": ("Lihat dan Sentuh", "ms 22–23", "capan dan kolaj", "dua sampel teknik"),
            "009": ("Kaktus Khatulistiwa", "ms 24–25", "montaj", "dua lapisan rupa"),
        }
        for pdp, (title, pages, technique, evidence) in cases.items():
            with self.subTest(pdp=pdp):
                row = by_pdp[pdp]
                self.assertEqual(row["Tajuk/aktiviti PdP"], title)
                self.assertIn(pages, row["Rujukan BT ms (RPT 2026)"])
                self.assertIn(evidence, row["Evidens PBD"])
                rph = (ROOT / row["RPH"]).read_text(encoding="utf-8")
                self.assertIn(title, rph)
                self.assertIn(pages, rph)
                self.assertIn(technique, rph)
                self.assertNotIn("garisan laluan, rupa rumah", rph)
                self.assertIn(row["Objektif"], rph)
        html = (PSV / "RPT_PSV_Tahun_6_2027_DRAF.html").read_text(encoding="utf-8")
        for pdp, (_, pages, _, _) in cases.items():
            with self.subTest(html_pdp=pdp):
                row = next(r for r in html.splitlines() if f"<td>{pdp}</td>" in r)
                self.assertIn(f"Buku teks {pages}", row)


    def test_year4_ten_objective_and_evidence_corrections(self):
        rows = read_csv(PSV / "RPT_PSV_Tahun_4_2027_DRAF.csv")
        corrected = {1, 5, 9, 13, 17, 22, 26, 30, 34, 38}
        self.assertEqual(len(rows), 42)
        for n in corrected:
            row = rows[n - 1]
            with self.subTest(pdp=n):
                self.assertEqual(row["PdP"], f"{n:03d}")
                rph = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                m = re.search(r"## Objektif dan kriteria kejayaan\nMurid dapat (.*?)\. (?:Evidens|Kriteria kejayaan): (.*?)\.", rph)
                self.assertIsNotNone(m)
                self.assertEqual(row["Objektif"], "Murid dapat " + m.group(1))
                self.assertEqual(row["Evidens PBD"], m.group(2))

    def test_year6_units_six_seven_are_textbook_specific(self):
        rows = read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")
        lookup = {row["PdP"]: row for row in rows}
        checks = {
            "019": ("Gerak Berirama", "52–53", "garisan beralun"),
            "020": ("Dompet Lemon Kesayanganku", "54–55", "resis"),
            "022": ("Ikatan Seni", "58–59", "ikatan"),
            "023": ("Sarung Botol Idamanku", "60–61", "sarung botol"),
        }
        activities = []
        for pdp, (title, pages, keyword) in checks.items():
            with self.subTest(pdp=pdp):
                row = lookup[pdp]
                self.assertEqual(row["Tajuk/aktiviti PdP"], title)
                self.assertIn(pages, row["Rujukan BT ms (RPT 2026)"])
                text = (ROOT / row["RPH"]).read_text(encoding="utf-8")
                self.assertIn(title, text)
                self.assertIn(keyword, text.lower())
                self.assertIn(row["Objektif"], text)
                self.assertIn(row["Evidens PBD"].rstrip("."), text)
                activity = re.search(r"\*\*Aktiviti 2[^\n]*\*\* ([^\n]+)", text)
                self.assertIsNotNone(activity)
                activities.append(activity.group(1))
        self.assertEqual(len(activities), len(set(activities)))
        html = (PSV / "RPT_PSV_Tahun_6_2027_DRAF.html").read_text(encoding="utf-8")
        for pdp, (title, pages, _) in checks.items():
            line = next(r for r in html.splitlines() if f"<td>{pdp}</td>" in r)
            self.assertIn(title, line)
            self.assertIn(f"Buku teks ms {pages}", line)

    def test_calendar_42_week_windows_without_full_school_breaks(self):
        windows = read_csv(PSV / "PSV_2027_minggu_PdP_kumpulan_A_B_CADANGAN.csv")
        self.assertEqual(len(windows), 42)
        # Dates are *week windows*, not exact teacher timetable or local public-holiday dates.
        breaks = {
            "A": [("2027-03-05", "2027-03-13"),
                  ("2027-05-21", "2027-06-05"),
                  ("2027-08-27", "2027-09-04"),
                  ("2027-02-07", "2027-02-11"),
                  ("2027-05-16", "2027-05-20")],
            "B": [("2027-03-06", "2027-03-14"),
                  ("2027-05-22", "2027-06-06"),
                  ("2027-08-28", "2027-09-05"),
                  ("2027-02-08", "2027-02-12"),
                  ("2027-05-17", "2027-05-21")],
        }
        for number, row in enumerate(windows, 1):
            self.assertEqual(row["PdP"], f"{number:03d}")
            self.assertEqual(row["Status"], "CADANGAN_MINGGU_2027")
            for group in ("A", "B"):
                start = date.fromisoformat(row[f"Minggu_{group}_mulai"])
                end = date.fromisoformat(row[f"Minggu_{group}_hingga"])
                self.assertLessEqual(start, end)
                self.assertLessEqual((end - start).days, 4)
                d = start
                while d <= end:
                    for left, right in breaks[group]:
                        self.assertFalse(date.fromisoformat(left) <= d <= date.fromisoformat(right),
                                         f"PdP {number}: {group} on school-break day {d}")
                    d += timedelta(days=1)
        self.assertEqual(windows[0]["Minggu_A_mulai"], "2027-01-04")
        self.assertEqual(windows[-1]["Minggu_B_hingga"], "2027-12-03")


    def test_no_false_ready_or_invented_exact_dates(self):
        # The staging branch has draft source documents, not a production-approved
        # schedule or validated one-page Word/PDF outputs. Keep the release gate shut.
        for year in range(2, 7):
            with self.subTest(year=year):
                rpt = read_csv(PSV / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv")
                self.assertEqual(len(rpt), 42)
                for row in rpt:
                    self.assertEqual(row["Status"], "DRAF_SEMAK")
                    self.assertFalse(row["Tarikh A"].strip())
                    self.assertFalse(row["Tarikh B"].strip())
                    path = row["RPH"] if year == 6 else row["Fail RPH"]
                    rph = (ROOT / path).read_text(encoding="utf-8")
                    self.assertIn("**Status:** DRAF", rph)
        windows = read_csv(PSV / "PSV_2027_minggu_PdP_kumpulan_A_B_CADANGAN.csv")
        self.assertEqual({row["Status"] for row in windows}, {"CADANGAN_MINGGU_2027"})


    def test_year6_verified_unit8_to10_12_lesson_repair(self):
        """Source-confirmed Unit 8–10 RPH, RPT and print HTML must agree."""
        by_pdp = {row["PdP"]: row for row in read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")}
        pages = {
            "028": ("64–65", "Cucuk Sanggul Sang Puteri", "kelopak"),
            "029": ("66–67", "Tanjak Seri Kencana", "lipatan"),
            "030": ("68–69", "Perkembangan idea", "peta idea"),
            "031": ("70–71", "Lakaran reka bentuk", "cerminan"),
            "032": ("72–73", "Penghasilan karya", "daun sirih"),
            "033": ("73–74", "Kemasan karya", "rambu"),
            "034": ("74–75", "Dokumentasi dan apresiasi", "galeri"),
            "035": ("76–77", "Perkembangan idea", "olahan motif"),
            "036": ("78–79", "Lakaran reka bentuk", "susunan corak"),
            "037": ("80–83", "Penghasilan karya", "resis"),
            "038": ("84–85", "Kemasan produk", "velkro"),
            "039": ("86–87", "Dokumentasi dan apresiasi", "galeri"),
        }
        html = (PSV / "RPT_PSV_Tahun_6_2027_DRAF.html").read_text(encoding="utf-8")
        activities = []
        for pdp, (page, activity_title, specific_term) in pages.items():
            with self.subTest(pdp=pdp):
                row = by_pdp[pdp]
                self.assertEqual(row["Tajuk/aktiviti PdP"], activity_title)
                self.assertEqual(row["Rujukan BT ms (RPT 2026)"], "Buku teks ms " + page)
                self.assertEqual(row["Status"], "DRAF_SEMAK")
                rph = (ROOT / row["RPH"]).read_text(encoding="utf-8")
                self.assertIn("ms " + page, rph)
                self.assertIn("**Aktiviti/Tajuk:** " + activity_title, rph)
                self.assertIn("**SK:** " + row["SK"], rph)
                self.assertIn("**SP:** " + row["SP"], rph)
                obj = re.search(r"(?m)^Murid dapat (.+?)\. Kriteria kejayaan: (.+?)\.$", rph)
                self.assertIsNotNone(obj)
                self.assertEqual(row["Objektif"], "Murid dapat " + obj.group(1))
                self.assertEqual(row["Evidens PBD"], obj.group(2))
                actual_activity = re.search(r"\*\*Aktiviti 2[^\n]*\*\* ([^\n]+)", rph)
                self.assertIsNotNone(actual_activity)
                self.assertIn(specific_term, actual_activity.group(1).lower())
                activities.append(actual_activity.group(1))
                line = next(line for line in html.splitlines() if "<td>" + pdp + "</td>" in line)
                self.assertIn("Buku teks ms " + page, line)
        self.assertEqual(len(activities), len(set(activities)))

    def test_year6_other_18_staging_criteria_are_measurable(self):
        """Earlier source drafts now name their concrete RPT PBD evidence."""
        by_pdp = {row["PdP"]: row for row in read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")}
        pdps = (1, 10, 11, 12, 13, 14, 15, 16, 17, 18, 21, 24, 25, 26, 27, 40, 41, 42)
        for number in pdps:
            pdp = f"{number:03d}"
            with self.subTest(pdp=pdp):
                row = by_pdp[pdp]
                rph = (ROOT / row["RPH"]).read_text(encoding="utf-8")
                expected = row["Evidens PBD"].rstrip(".")
                self.assertIn("Kriteria kejayaan: " + expected + ".", rph)
                self.assertNotIn("hasil kerja individu atau kumpulan memperlihatkan evidens", rph)
                self.assertIn("**Status:** DRAF", rph)


    def test_all_210_sp_codes_exist_in_verified_dskp_source(self):
        """Necessary code-presence check; semantics still require lesson review."""
        manifest = json.loads((PSV / "dskp_sp_code_presence_audit_20261105.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["years"]), {str(y) for y in range(2, 7)})
        for year in range(2, 7):
            with self.subTest(year=year):
                rows = read_csv(PSV / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv")
                used = {code.strip() for row in rows for code in row["SP"].split(";") if code.strip()}
                expected = set(manifest["years"][str(year)]["used_sp_codes"])
                self.assertEqual(len(rows), 42)
                self.assertEqual(manifest["years"][str(year)]["rpt_rows"], 42)
                self.assertEqual(used, expected)

    def test_year4_harum_mewangi_actual_soap_relief_and_pbd(self):
        rows = read_csv(PSV / "RPT_PSV_Tahun_4_2027_DRAF.csv")
        evidence = {
            "038": ("96–97", "lekukan"),
            "039": ("98–99", "sudu"),
            "040": ("98–99", "kain net"),
        }
        for pdp, (page, material) in evidence.items():
            with self.subTest(pdp=pdp):
                row = rows[int(pdp) - 1]
                rph = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                self.assertIn("Harum Mewangi", rph)
                self.assertIn("ms " + page, rph)
                self.assertIn(material, rph)
                self.assertIn("alat tumpul", rph)
                self.assertIn("**Status:** DRAF", rph)
                objective = re.search(
                    r"(?m)^Murid dapat (.*?)\. Kriteria kejayaan: (.*?)\.$", rph
                )
                self.assertIsNotNone(objective)
                self.assertEqual(row["Objektif"], "Murid dapat " + objective.group(1))
                self.assertEqual(row["Evidens PBD"], objective.group(2))

    def test_year5_original_textbook_selected_units_use_exact_materials_and_sources(self):
        """Check visually grounded Year 5 fixes without claiming all 42 pages reviewed."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_5_2027_DRAF.csv")
        source = "https://drive.google.com/file/d/1UA9arc9LrigHx-GccSJFpkTtqfskLFpg/view"
        self.assertEqual(len(rows), 42)
        self.assertTrue(all(row["Pautan Buku Teks"] == source for row in rows))
        expected = {
            17: ("38–41", "terapan", "lingkaran"),
            18: ("42–43", "tiga lingkaran", "tapak"),
            19: ("44–45", "timbul", "terapan"),
            34: ("74–75", "imbangan", "tapak"),
            35: ("76–77", "polistirena", "tapak"),
            36: ("78–79", "polistirena", "10 saat"),
            37: ("80–81", "tapak berlapis", "10 saat"),
            38: ("82–85", "mempulur", "tekat"),
            39: ("86–87", "mempulur", "jarum sulam tumpul"),
            40: ("88–89", "tekat timbul", "benang"),
        }
        for number, (page, term_a, term_b) in expected.items():
            with self.subTest(pdp=number):
                row = rows[number - 1]
                raw = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                self.assertIn("ms " + page, raw)
                self.assertIn(term_a.lower(), raw.lower())
                self.assertIn(term_b.lower(), raw.lower())
                self.assertIn(source, raw)
                self.assertIn("**Status:** DRAF", raw)
        for number in range(34, 38):
            raw = (ROOT / f"rph_standalone/psv/year5/lesson_{number:03d}.md").read_text(encoding="utf-8")
            self.assertNotIn("batang kertas", raw)
            self.assertIn("guru", raw.lower())

    def test_year5_original_pdf_swan_and_frame_workflow(self):
        """Ensure textbook-specific art and safe titisan stay in RPH after edits."""
        checks = {
            1: ("angsa", "capan", "putik kapas"),
            2: ("angsa", "lakaran", "capan"),
            3: ("angsa", "latar", "garisan"),
            4: ("angsa", "bingkai", "bulu"),
            30: ("titisan", "pipet", "tanpa lilin panas"),
            31: ("ketinggian", "pipet", "tanpa lilin panas"),
            32: ("panel", "pipet", "kering"),
            33: ("bingkai", "lipatan", "penyangga"),
        }
        rows = read_csv(PSV / "RPT_PSV_Tahun_5_2027_DRAF.csv")
        for n, phrases in checks.items():
            with self.subTest(pdp=n):
                text = (ROOT / f"rph_standalone/psv/year5/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(term in text for term in phrases))
                self.assertEqual(rows[n - 1]["Status"], "DRAF_SEMAK")
                self.assertIn("1UA9arc9LrigHx-GccSJFpkTtqfskLFpg".lower(), text)

    def test_year5_pdf_units_2_to_4_have_concrete_pupil_artwork(self):
        """Source-specific artifacts and source link for 2026-11-05 PDF review."""
        checks = {
            5: ("poster", "ikan bayan"), 6: ("ikan bayan", "slogan"),
            7: ("montaj", "ikan bayan"), 8: ("selamatkan ikan bayan", "galeri"),
            9: ("kolaj", "kupu-kupu"), 10: ("motif", "kapal layar"),
            11: ("kapal layar", "kolaj"), 12: ("kapal layar", "jaket"),
            13: ("roket", "silinder"), 14: ("roket", "botol"),
            15: ("kon", "botol plastik"), 16: ("sayap", "roket"),
        }
        for n, required in checks.items():
            with self.subTest(pdp=n):
                text = (ROOT / f"rph_standalone/psv/year5/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(k in text for k in required))
                self.assertIn("1UA9arc9LrigHx-GccSJFpkTtqfskLFpg".lower(), text)
                self.assertIn("**status:** draf", text)

    def test_year5_pdf_units_6_and_7_and_project_source_positions(self):
        """Check concrete media and project-placement honesty in Year 5."""
        required = {
            20: ("ms 4–5", "cadangan cikgulaju"),
            21: ("ms 4–5", "cadangan cikgulaju"),
            22: ("pungguk", "gurisan"), 23: ("gurisan", "kolaj"),
            24: ("pungguk", "oil pastel"), 25: ("pungguk", "bingkai"),
            26: ("kekwa", "catan"), 27: ("mozek", "catan"),
            28: ("mozek", "kelopak"), 29: ("mozek", "bingkai"),
            41: ("ms 46–49", "cadangan cikgulaju"),
            42: ("ms 46–49", "cadangan cikgulaju"),
        }
        for n, terms in required.items():
            with self.subTest(pdp=n):
                body = (ROOT / f"rph_standalone/psv/year5/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(term in body for term in terms))
                self.assertIn("1UA9arc9LrigHx-GccSJFpkTtqfskLFpg".lower(), body)
                self.assertIn("**status:** draf", body)

    def test_year4_original_pdf_artwork_repairs_remain_staging_only(self):
        """Textbook-specific source, technique, student product and release gating."""
        checks = {
            5: ("mozek", "bersebelahan"), 6: ("paper quilling", "gulung"),
            7: ("paper quilling", "batang aiskrim"), 8: ("gulungan", "imbangan"),
            9: ("stensil", "kemeja-t"), 10: ("kemeja-t", "motif"),
            11: ("kemeja-t", "stensilan"), 12: ("kemeja-t", "beg"),
            13: ("bunga matahari", "penutup botol"),
            14: ("penutup botol", "kelopak"), 15: ("bunga matahari", "kepala"),
            16: ("gulungan tisu", "botol"), 17: ("cawan", "piring"),
            18: ("cawan", "piring"), 19: ("pemegang", "piring"),
            20: ("ms 4–5", "unit 1"), 21: ("ms 4–5", "unit 1"),
            30: ("pualaman", "krim"), 31: ("pewarna makanan", "pelarut"),
            32: ("pualaman", "kering"), 33: ("arnab", "tempat letak telefon"),
            41: ("ms 54–55", "unit 10"), 42: ("ms 54–55", "unit 10"),
        }
        rows = read_csv(PSV / "RPT_PSV_Tahun_4_2027_DRAF.csv")
        self.assertEqual(len(rows), 42)
        for n, keywords in checks.items():
            with self.subTest(pdp=n):
                body = (ROOT / f"rph_standalone/psv/year4/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(k in body for k in keywords))
                self.assertIn("1zpvbjcwogzvqjrsgpmsgd6iymmxcassu", body)
                self.assertIn("**status:** draf", body)
                self.assertEqual(rows[n-1]["Status"], "DRAF_SEMAK")
        self.assertTrue(all(row["Pautan Buku Teks"] == "https://drive.google.com/file/d/1ZPvbJcwogZVQjRSgPMSgD6iymMXcASSU/view" for row in rows))

    def test_year2_source_paged_pottery_fruit_rubbings_and_marine_resis(self):
        """Guard source-specific Y2 lessons and page range mapping."""
        sources = {
            18: ("40–41", "buah", "gosokan"),
            19: ("40–41", "buah", "gosokan"),
            31: ("66–67", "picitan", "tembikar"),
            32: ("68–69", "picitan", "tembikar"),
            33: ("68–69", "tembikar", "kering"),
            35: ("76–77", "taman mini", "bunga"),
            36: ("78–79", "taman mini", "rama-rama"),
            37: ("78–79", "taman mini", "bunga"),
            39: ("88–89", "suasana hidupan laut", "resis"),
            40: ("88–89", "suasana hidupan laut", "resis"),
        }
        rows = read_csv(PSV / "RPT_PSV_Tahun_2_2027_DRAF.csv")
        for n, (pages, a, b) in sources.items():
            with self.subTest(pdp=n):
                text = (ROOT / f"rph_standalone/psv/year2/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(w in text for w in (a, b)))
                self.assertIn("ms " + pages, text)
                self.assertIn(pages, rows[n-1]["BT muka surat"])
                self.assertEqual(rows[n-1]["Status"], "DRAF_SEMAK")

    def test_year6_real_textbook_project_pages_not_photo_book(self):
        """Printed book has exhibition projects p4-5 and p46-49; p88-89 is a photo book."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")
        html = (PSV / "RPT_PSV_Tahun_6_2027_DRAF.html").read_text(encoding="utf-8")
        for number, page, term in [(24, "4–5", "penggal satu"), (25, "4–5", "penggal satu"),
                                   (26, "4–5", "penggal satu"), (40, "46–49", "penggal dua"),
                                   (41, "46–49", "penggal dua"), (42, "46–49", "penggal dua")]:
            with self.subTest(pdp=number):
                row = rows[number - 1]
                raw = (ROOT / f"rph_standalone/psv/year6/lesson_{number:03d}.md").read_text(encoding="utf-8").lower()
                self.assertIn("ms " + page, raw)
                self.assertIn(term, raw)
                self.assertIn("turutan cadangan cikgulaju", raw)
                self.assertIn(page, row["Rujukan BT ms (RPT 2026)"])
                self.assertEqual(row["Status"], "DRAF_SEMAK")
                self.assertIn("<td>" + f"{number:03d}" + "</td>", html)
                self.assertIn(row["Rujukan BT ms (RPT 2026)"], html)
        for number in (40, 41, 42):
            self.assertIn("buku foto ms 88–89", rows[number-1]["Rujukan BT ms (RPT 2026)"].lower())

    def test_year3_original_textbook_sticks_lampshade_weaving_and_exhibitions(self):
        """Source-specific craft outcomes from printed Y3 textbook pages."""
        expectations = {
            30: ("ms 66–67", "renjisan", "jalinan"),
            31: ("ms 68–69", "batang aiskrim", "renjisan"),
            32: ("ms 68–69", "empat rangka", "terendak lampu"),
            33: ("ms 68–69", "lilin elektronik", "tiada nyalaan api"),
            38: ("ms 86–87", "kelarai", "anyaman"),
            39: ("ms 88–90", "kertas a", "alas mangkuk"),
            40: ("ms 90–91", "alas mangkuk", "kelarai"),
            20: ("ms 4–5", "unit 1", "adaptasi"),
            21: ("ms 4–5", "unit 1", "adaptasi"),
            41: ("ms 48–49", "unit 10", "adaptasi"),
            42: ("ms 48–49", "unit 10", "adaptasi"),
        }
        rpt = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        for n, bits in expectations.items():
            with self.subTest(pdp=n):
                raw = (ROOT / f"rph_standalone/psv/year3/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(bit in raw for bit in bits))
                self.assertIn("hkvtu/vifc", raw)
                self.assertEqual(rpt[n-1]["Status"], "DRAF_SEMAK")
                if n == 32:
                    self.assertEqual(rpt[n-1]["BT muka surat"], "68–69")
                if n in (20, 21, 41, 42):
                    self.assertIn("Projek Penggal", rpt[n-1]["BT muka surat"])

    def test_year6_original_book_koi_stabail_must_rotate_safely(self):
        """Koi is a functional rotating stabail, not a static paper fish."""
        for n in (14, 15, 16, 17):
            with self.subTest(pdp=n):
                text = (ROOT / f"rph_standalone/psv/year6/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertIn("berpusing", text)
                self.assertIn("roda", text)
                self.assertIn("prasiap guru", text)
                self.assertIn("**status:** draf", text)
        work = (ROOT / "rph_standalone/psv/year6/lesson_016.md").read_text(encoding="utf-8").lower()
        self.assertIn("tanpa bergesel atau tumbang", work)
        end = (ROOT / "rph_standalone/psv/year6/lesson_017.md").read_text(encoding="utf-8").lower()
        self.assertIn("folio sumber idea", end)
        self.assertIn("gambar akhir", end)

    def test_year3_poster_perayaan_and_selempang_pancar_match_original_textbook(self):
        """Guard original book outcome and consistency of precise RPH and RPT anchors."""
        expected = {
            5: ("14–15", "poster perayaan", "ruang"),
            6: ("16–17", "poster perayaan", "muka taip"),
            7: ("16–17", "poster perayaan", "tiga imej"),
            8: ("16–17", "poster perayaan", "galeri"),
            9: ("22–23", "saderi", "bendi"),
            10: ("24–25", "selempang pancar", "saderi"),
            11: ("24–25", "selempang pancar", "kain putih"),
            12: ("24–25", "selempang pancar", "motif pancaran"),
        }
        rpt = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        html = (PSV / "RPT_PSV_Tahun_3_2027_DRAF.html").read_text(encoding="utf-8")
        self.assertEqual(len(rpt), 42)
        for number, (page, art, process) in expected.items():
            with self.subTest(pdp=number):
                row = rpt[number - 1]
                content = (ROOT / f"rph_standalone/psv/year3/lesson_{number:03d}.md").read_text(encoding="utf-8")
                self.assertIn("ms " + page, content)
                self.assertIn(page, row["BT muka surat"])
                self.assertIn(art, content.lower())
                self.assertIn(process, content.lower())
                self.assertIn(row["Objektif"], content)
                self.assertIn(row["Evidens PBD"], content)
                self.assertEqual(row["Status"], "DRAF_SEMAK")
                self.assertIn("hkvtu/vifc", content)
        for number, page in ((7, "16–17"), (11, "24–25")):
            id = f"{number:03d}"
            line = next(line for line in html.splitlines() if f"<td>{id}</td>" in line)
            self.assertIn(f"<td>{page}</td>", line)

    def test_year3_serangga_kecil_mobail_matches_book_30_to_35(self):
        """Concrete asemblaj hanging shapes plus paper-cup tie, not generic cardboard."""
        checks = {
            13: ("30–31", "asemblaj", "serangga"),
            14: ("32–33", "ikatan", "cawan kertas"),
            15: ("34–35", "cawan kertas", "pratebuk"),
            16: ("34–35", "simpulan tali", "mobail"),
        }
        rpt = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        html = (PSV / "RPT_PSV_Tahun_3_2027_DRAF.html").read_text(encoding="utf-8")
        for n, terms in checks.items():
            with self.subTest(pdp=n):
                content = (ROOT / f"rph_standalone/psv/year3/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(w in content for w in terms))
                self.assertEqual(rpt[n-1]["Status"], "DRAF_SEMAK")
                self.assertIn(rpt[n-1]["Objektif"].lower(), content)
                self.assertIn(rpt[n-1]["Evidens PBD"].lower(), content)
        self.assertEqual(rpt[14]["BT muka surat"], "34–35")
        self.assertIn("<td>015</td>", html)
        self.assertIn("<td>34–35</td>", html)

    def test_year3_boneka_tali_matches_original_textbook_product(self):
        """The Year 3 book makes a string puppet, not a stick puppet."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        expected = {
            34: ("74–75", "boneka tali", "jalinan"),
            35: ("76–77", "gulungan tisu", "tali"),
            36: ("78–79", "penyedut minuman", "tangan dan kaki"),
            37: ("78–79", "boneka tali", "pergerakan"),
        }
        for n, (pages, media, task) in expected.items():
            with self.subTest(pdp=n):
                row = rows[n-1]
                body = (ROOT / f"rph_standalone/psv/year3/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertTrue(all(x in body for x in (media, task)))
                self.assertIn("ms " + pages, body)
                self.assertIn(pages, row["BT muka surat"])
                self.assertIn(row["Objektif"].lower(), body)
                self.assertIn(row["Evidens PBD"].lower(), body)
                self.assertIn("**status:** draf", body)
        body = (ROOT / "rph_standalone/psv/year3/lesson_036.md").read_text(encoding="utf-8").lower()
        self.assertNotIn("boneka tongkat", body)

    def test_year3_kad_untukmu_burung_merak_source_specific(self):
        """Year 3 unit 7 produces a scratched greeting card, not a generic drawing."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        for n in (26, 27, 28, 29):
            with self.subTest(pdp=n):
                content = (ROOT / f"rph_standalone/psv/year3/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertIn("oil pastel", content)
                self.assertIn("batang aiskrim", content)
                self.assertIn("gurisan", content)
                self.assertIn(rows[n-1]["Objektif"].lower(), content)
                self.assertIn(rows[n-1]["Evidens PBD"].lower(), content)
                self.assertIn("**status:** draf", content)
        card = (ROOT / "rph_standalone/psv/year3/lesson_028.md").read_text(encoding="utf-8").lower()
        self.assertIn("kad untukmu", card)
        self.assertIn("burung merak", card)
        self.assertIn("ms 60–61", card)
        self.assertEqual(rows[27]["BT muka surat"], "60–61")

    def test_year3_belon_udara_kolaj_from_original_textbook(self):
        """Keep specific torn-paper, magazine and felt collage process, page reference and draft gating."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        for n in (22, 23, 24, 25):
            with self.subTest(pdp=n):
                text = (ROOT / f"rph_standalone/psv/year3/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertIn("belon udara", text)
                self.assertIn("majalah", text)
                self.assertIn("kain felt", text)
                self.assertIn(rows[n-1]["Objektif"].lower(), text)
                self.assertIn(rows[n-1]["Evidens PBD"].lower(), text)
                self.assertEqual(rows[n-1]["Status"], "DRAF_SEMAK")
        lesson = (ROOT / "rph_standalone/psv/year3/lesson_024.md").read_text(encoding="utf-8").lower()
        self.assertIn("ms 52–53", lesson)
        self.assertIn("secara bertindih", lesson)
        self.assertEqual(rows[23]["BT muka surat"], "52–53")

    def test_year3_original_book_train_roda_smoke_and_crosshatch(self):
        """Actual train crosshatching uses wheel perspective and smoke movement, not generic lines."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        for n in (1, 2, 3, 4):
            with self.subTest(pdp=n):
                text = (ROOT / f"rph_standalone/psv/year3/lesson_{n:03d}.md").read_text(encoding="utf-8").lower()
                self.assertIn("silang pangkah", text)
                self.assertIn("roda", text)
                if n in (2, 3, 4):
                    self.assertIn("asap", text)
                self.assertIn(rows[n-1]["Objektif"].lower(), text)
                self.assertIn(rows[n-1]["Evidens PBD"].lower(), text)
                self.assertEqual(rows[n-1]["Status"], "DRAF_SEMAK")
        self.assertEqual(rows[2]["BT muka surat"], "8–9")
        body = (ROOT / "rph_standalone/psv/year3/lesson_003.md").read_text(encoding="utf-8")
        self.assertIn("ms 8–9", body)

    def test_year3_parang_ilang_art_is_inert_layered_heritage_model(self):
        """Source-specific craft and safety, never a functional sharp weapon."""
        rows = read_csv(PSV / "RPT_PSV_Tahun_3_2027_DRAF.csv")
        for number in (17, 18, 19):
            with self.subTest(pdp=number):
                body = (ROOT / f"rph_standalone/psv/year3/lesson_{number:03d}.md").read_text(encoding="utf-8").lower()
                self.assertIn("parang ilang", body)
                self.assertIn("tali rafia", body)
                self.assertIn("kadbod", body)
                self.assertIn("tanpa bilah tajam", body)
                self.assertIn(rows[number-1]["Objektif"].lower(), body)
                self.assertIn(rows[number-1]["Evidens PBD"].lower(), body)
                self.assertEqual(rows[number-1]["Status"], "DRAF_SEMAK")
        self.assertEqual(rows[17]["BT muka surat"], "42–43")
        body = (ROOT / "rph_standalone/psv/year3/lesson_018.md").read_text(encoding="utf-8")
        self.assertIn("ms 42–43", body)
        self.assertIn("tidak berfungsi", body)

    def test_year5_bunga_kemboja_tekat_is_genuine_couching(self):
        rows = read_csv(PSV / "RPT_PSV_Tahun_5_2027_DRAF.csv")
        keywords = {
            "038": ("82–85", "mempulur"),
            "039": ("86–87", "jarum sulam tumpul"),
            "040": ("88–89", "tekat timbul"),
        }
        for pdp, (page, keyword) in keywords.items():
            with self.subTest(pdp=pdp):
                row = rows[int(pdp) - 1]
                rph = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                self.assertIn("Bunga Kemboja Emas", rph)
                self.assertIn("ms " + page, rph)
                self.assertIn(keyword, rph)
                self.assertNotIn("simulasi tekat", rph.lower())
                self.assertNotIn("coba susunan", rph.lower())
                self.assertIn("**Status:** DRAF", rph)
                objective = re.search(
                    r"(?m)^Murid dapat (.*?)\. Kriteria kejayaan: (.*?)\.$", rph
                )
                self.assertIsNotNone(objective)
                self.assertEqual(row["Objektif"], "Murid dapat " + objective.group(1))
                self.assertEqual(row["Evidens PBD"], objective.group(2))


    def test_year6_sp311_requires_folio_not_only_photo(self):
        """DSKP Tahun 6: SP3.1.1 demands a folio for all four product projects."""
        for number in (13, 17, 34, 39):
            with self.subTest(pdp=number):
                pdp = f"{number:03d}"
                rph = (ROOT / "rph_standalone" / "psv" / "year6" / f"lesson_{pdp}.md").read_text(encoding="utf-8")
                self.assertIn("**SP:** 3.1.1; 3.2.3; 4.1.1", rph)
                self.assertIn("folio", rph.lower())
                activity = re.search(r"(?m)^\*\*Aktiviti 2[^\n]*\*\*\s*(.*)$", rph)
                self.assertIsNotNone(activity)
                self.assertIn("folio", activity.group(1).lower())
        csv_rows = read_csv(PSV / "RPT_PSV_Tahun_6_2027_DRAF.csv")
        for number in (34, 39):
            with self.subTest(pdp=number):
                row = csv_rows[number - 1]
                text = (ROOT / row["RPH"]).read_text(encoding="utf-8")
                match = re.search(r"(?m)^Murid dapat (.*?)\. Kriteria kejayaan: (.*?)\.$", text)
                self.assertIsNotNone(match)
                self.assertIn("folio lima bahagian", row["Evidens PBD"])
                self.assertEqual(row["Objektif"], "Murid dapat " + match.group(1))
                self.assertEqual(row["Evidens PBD"], match.group(2))

    def test_project_printed_sp_codes_are_clean_for_public_headers(self):
        """Y2–4 original DSKP prints 3.3.x below SK 5.1; no audit note in headers."""
        for year in (2, 3, 4):
            rows = read_csv(PSV / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv")
            for number in (20, 21, 41, 42):
                with self.subTest(year=year, pdp=number):
                    row = rows[number - 1]
                    source = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                    sp = re.search(r"(?m)^\*\*SP:\*\*\s*([^\n]+)", source)
                    self.assertIsNotNone(sp)
                    self.assertEqual(sp.group(1).strip(), row["SP"])
                    self.assertEqual(row["SK"], "5.1")
                    self.assertTrue(row["SP"].startswith("3.3."))
                    self.assertNotIn("kod bercetak", sp.group(1))
                    self.assertNotIn("bercetak di bawah", sp.group(1))


    def test_forty_unit_dskp_technique_and_production_semantics(self):
        """Independent SP-to-technique crosswalk from printed Y2–Y5 DSKP.

        This checks real teaching activity text, never just title metadata.
        Y2 DSKP prints SP 2.1.3 twice, covering both construction and
        traditional craft; retain original printed code, not a made-up 2.1.4.
        """
        verified = {
            2: [
                ("2.1.1", "3.1.1", r"garisan selari"),
                ("2.1.2", "3.1.1", r"lipatan|guntingan"),
                ("2.1.3", "3.1.1", r"stabail"),
                ("2.1.3", "3.1.1", r"gasing"),
                ("2.1.1", "3.1.1", r"gosokan"),
                ("2.1.2", "3.1.1", r"cetakan|cetak"),
                ("2.1.3", "3.1.1", r"topeng"),
                ("2.1.3", "3.1.1", r"tembikar|picitan"),
                ("2.1.1", "3.1.1", r"basah atas kering|rama.rama"),
                ("2.1.1", "3.1.1", r"resis"),
            ],
            3: [
                ("2.1.1", "3.1.1", r"silang pangkah"),
                ("2.1.1", "3.1.1", r"montaj|bertindih"),
                ("2.1.2", "3.1.2", r"capan"),
                ("2.1.3", "3.1.4", r"mobail"),
                ("2.1.4", "3.1.5", r"parang ilang|alat pertahanan"),
                ("2.1.1", "3.1.1", r"kolaj"),
                ("2.1.1", "3.1.1", r"gurisan"),
                ("2.1.2", "3.1.2", r"renjisan|percikan"),
                ("2.1.3", "3.1.4", r"boneka"),
                ("2.1.4", "3.1.5", r"anyaman"),
            ],
            4: [
                ("2.1.1", "3.1.1", r"basah atas basah"),
                ("2.1.2", "3.1.1", r"mozek"),
                ("2.1.6", "3.1.3", r"stensil"),
                ("2.1.7", "3.1.4", r"asemblaj"),
                ("2.1.10", "3.1.5", r"papier.mache|cawan"),
                ("2.1.3", "3.1.1", r"poster"),
                ("2.1.4", "3.1.1", r"kolograf"),
                ("2.1.5", "3.1.3", r"pualaman"),
                ("2.1.8", "3.1.4", r"diorama"),
                ("2.1.9", "3.1.5", r"ukiran"),
            ],
            5: [
                ("2.1.4", "3.1.1", r"capan"),
                ("2.1.2", "3.1.1", r"montaj|poster"),
                ("2.1.6", "3.1.3", r"kolaj"),
                ("2.1.8", "3.1.4", r"roket|model"),
                ("2.1.9", "3.1.5", r"tembikar|paper.clay|pasu"),
                ("2.1.1", "3.1.1", r"gurisan|kolaj"),
                ("2.1.3", "3.1.1", r"mozek|catan"),
                ("2.1.5", "3.1.3", r"titisan"),
                ("2.1.7", "3.1.4", r"stabail"),
                ("2.1.10", "3.1.5", r"tekat|mempulur"),
            ],
        }
        checked = 0
        for year, units in verified.items():
            self.assertEqual(len(units), 10)
            rows = read_csv(PSV / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv")
            unit_steps = {n: [] for n in range(1, 11)}
            for row in rows:
                unit_raw = str(row["Unit"]).strip()
                if not unit_raw.isdecimal():
                    continue
                unit = int(unit_raw)
                with self.subTest(year=year, pdp=row["PdP"], unit=unit):
                    exploration, production, activity_pattern = units[unit - 1]
                    codes = [x.strip() for x in row["SP"].split(";")]
                    for code in codes:
                        if code.startswith("2.1."):
                            self.assertEqual(code, exploration)
                        if code.startswith("3.1."):
                            self.assertEqual(code, production)
                    rph = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                    activity = rph.partition("## Langkah PdP")[2]
                    self.assertTrue(activity, "Missing lesson activity section")
                    self.assertGreater(len(activity), 300)
                    unit_steps[unit].append(activity.lower())
                    checked += 1
            for unit, (_, _, activity_pattern) in enumerate(units, 1):
                with self.subTest(year=year, unit=unit):
                    self.assertRegex(" ".join(unit_steps[unit]), activity_pattern)
                    self.assertGreaterEqual(len(unit_steps[unit]), 3)
        self.assertEqual(checked, 152)



    def test_candidate_ci_content_repair_year4_and_year6(self):
        """Verify CI-driven teacher/pupil and PBD corrections, not just SP codes."""
        yr4 = read_csv(PSV / "RPT_PSV_Tahun_4_2027_DRAF.csv")
        for n in (20, 21, 41, 42):
            with self.subTest(year=4, pdp=n):
                row = yr4[n - 1]
                rph = (ROOT / row["Fail RPH"]).read_text(encoding="utf-8")
                self.assertIn("Kriteria kejayaan:", rph)
                m = re.search(
                    r"(?m)^(Murid dapat [^.]+)\. Kriteria kejayaan: ([^.]+)\.$",
                    rph,
                )
                self.assertIsNotNone(m)
                self.assertEqual(row["Objektif"], m.group(1))
                self.assertEqual(row["Evidens PBD"], m.group(2))
                self.assertIn("**SK:** 5.1", rph)
                self.assertNotIn("Bukti: pelan, kapsyen, foto dan senarai semak", rph)
        wet = (ROOT / "rph_standalone/psv/year4/lesson_001.md").read_text(encoding="utf-8")
        self.assertIn("catan basah atas basah:", wet.lower())
        gallery = (ROOT / "rph_standalone/psv/year6/lesson_039.md").read_text(encoding="utf-8")
        self.assertIn("folio dalam galeri mini", gallery.lower())


    def test_all_210_source_page_anchors_match_50_units(self):
        """Regression gate for correct textbook page and unit, not full page audit.

        The source-map page boundaries are from the 2026 RPT and named textbook
        units. This does not claim a visual examination of each textbook page.
        """
        anchors = json.loads(
            (PSV / "textbook_dskp_source_map_20261104.json").read_text(encoding="utf-8")
        )["years"]
        total, specific, exhibitions = 0, 0, 0
        page = re.compile(r"(?<!\d)(\d{1,3})\s*[-–]\s*(\d{1,3})(?!\d)")
        def page_bounds(value, *, require_ms=False):
            # Prefer the cited page over a parenthesized unit range.
            # A single page such as 'ms 8' is a precise valid anchor.
            pattern = (
                r"(?i)\bms\.?\s*(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?(?!\d)"
                if require_ms else
                r"(?i)(?:\bms\.?\s*|^\s*)(\d{1,3})(?:\s*[-–]\s*(\d{1,3}))?(?!\d)"
            )
            match = re.search(pattern, str(value))
            return (int(match.group(1)), int(match.group(2) or match.group(1))) if match else None
        for year in range(2, 7):
            source = anchors[str(year)]
            self.assertEqual(len(source["units"]), 10)
            rows = read_csv(PSV / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv")
            self.assertEqual(len(rows), 42)
            for pdp, row in enumerate(rows, 1):
                with self.subTest(year=year, pdp=pdp):
                    field = row.get("Unit") if year <= 5 else row.get("Unit 2026")
                    file = row.get("Fail RPH") if year <= 5 else row.get("RPH")
                    self.assertEqual(file, f"rph_standalone/psv/year{year}/lesson_{pdp:03d}.md")
                    raw = (ROOT / file).read_text(encoding="utf-8")
                    self.assertIn(f"Tahun {year} — PdP {pdp:03d}", raw)
                    if not str(field).isdecimal():
                        self.assertIn("pameran", raw.casefold())
                        exhibitions += 1
                        total += 1
                        continue
                    unit = int(field)
                    self.assertTrue(1 <= unit <= 10)
                    title, technique, span = source["units"][unit - 1][:3]
                    m = re.search(
                        r"(?m)^\*\*Unit(?: RPT 2026)?:\*\*\s*(?:Unit\s*)?"
                        r"(\d+)\s*[—–-]\s*(.+?)\s*$",
                        raw,
                    )
                    self.assertIsNotNone(m, "RPH has no identifiable textbook unit")
                    self.assertEqual(int(m.group(1)), unit)
                    self.assertEqual(normalize_title(m.group(2)),
                                     normalize_title(title))
                    section = re.search(
                        r"(?m)^\*\*(?:Rujukan )?Buku Teks:\*\*\s*([^\n]+)",
                        raw,
                    )
                    self.assertIsNotNone(section, "RPH has no explicit textbook page")
                    unit_range = page.search(span)
                    cited_range = page_bounds(section.group(1), require_ms=True)
                    self.assertIsNotNone(unit_range)
                    self.assertIsNotNone(cited_range)
                    a, b = map(int, unit_range.groups())
                    c, d = cited_range
                    self.assertLessEqual(a, c)
                    self.assertLessEqual(d, b)
                    self.assertLessEqual(c, d)
                    rpt_ref = (
                        row.get("BT muka surat", "")
                        if year < 6 else row.get("Rujukan BT ms (RPT 2026)", "")
                    )
                    rpt_page = page_bounds(rpt_ref, require_ms=(year == 6))
                    self.assertIsNotNone(rpt_page)
                    r1, r2 = rpt_page
                    self.assertLessEqual(a, r1)
                    self.assertLessEqual(r2, b)
                    self.assertLessEqual(r1, r2)
                    self.assertEqual((c, d), (r1, r2),
                                     "RPH/RPT must cite the same exact pages")
                    specific += 1
                    total += 1
        self.assertEqual(total, 210)
        self.assertEqual(specific, 188)
        self.assertEqual(exhibitions, 22)


if __name__ == "__main__":
    unittest.main()
