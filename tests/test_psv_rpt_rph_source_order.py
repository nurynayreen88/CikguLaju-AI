"""Regression checks for PSV 2027 draft source order and Year 5 RPT objective alignment.

Read-only: this suite never modifies application data or production assets.
Run with: python -m unittest tests.test_psv_rpt_rph_source_order
"""
import csv
import re
import unittest
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
                match = re.fullmatch(r"(Murid dapat .*?)\s+Evidens:\s+(.*)", " ".join(section.group(1).split()))
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
            "002": ("Alat Tulis Saya", "ms 10–11", "garisan selari", "dua lakaran alat tulis"),
            "003": ("Tingkap Damai", "ms 12–13", "tetingkap fokus", "tiga bahagian ruang"),
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
        self.assertIn("Buku teks ms 10–11", html)
        self.assertIn("Buku teks ms 12–13", html)


if __name__ == "__main__":
    unittest.main()
