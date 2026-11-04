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


if __name__ == "__main__":
    unittest.main()
