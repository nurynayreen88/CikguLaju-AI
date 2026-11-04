"""Non-destructive PSV staging consistency checks; run: python -m unittest tests.test_psv_rpt_rph_alignment."""
import csv
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
YEARS = (2, 3, 4, 5, 6)

class PsvAlignmentTests(unittest.TestCase):
    def test_rpt_and_rph_one_to_one(self):
        found = []
        for year in YEARS:
            rpt = ROOT / "rpt_2027" / "psv" / f"RPT_PSV_Tahun_{year}_2027_DRAF.csv"
            self.assertTrue(rpt.is_file(), f"Missing RPT: {rpt}")
            with rpt.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 42, f"Tahun {year}: unexpected PdP count")
            paths = []
            for index, row in enumerate(rows, start=1):
                number = f"{index:03d}"
                self.assertEqual(row["PdP"], number)
                path = row["Fail RPH"] if year < 6 else row["RPH"]
                expected = f"rph_standalone/psv/year{year}/lesson_{number}.md"
                self.assertEqual(path, expected)
                paths.append(path)
                file_path = ROOT / path
                self.assertTrue(file_path.is_file(), f"Missing RPH {path}")
                text = file_path.read_text(encoding="utf-8")
                self.assertIn(f"# RPH Pendidikan Seni Visual Tahun {year} — PdP {number}", text)
                for field in ("SK", "SP"):
                    escaped = re.escape(row[field])
                    self.assertRegex(text, rf"(?m)^\*\*{field}:\*\* {escaped}(?:\s|$)")
                unit_title = row["Tajuk karya cadangan"] if year < 6 else row["Tajuk unit"]
                self.assertIn(unit_title, text, f"Tahun {year} PdP {number}: unit mismatch")
                for expected_heading in ("## Objektif", "Set induksi", "Aktiviti 1",
                                         "Aktiviti 2", "Pentaksiran", "Penutup"):
                    self.assertIn(expected_heading, text)
                self.assertEqual(row["Status"], "DRAF_SEMAK")
                found.append(path)
            self.assertEqual(len(paths), len(set(paths)))
            crosswalk = ROOT / "rpt_2027" / "psv" / f"crosswalk_2026_tahun{year}_VERIFIED_SOURCE.csv"
            self.assertTrue(crosswalk.is_file())
            with crosswalk.open(encoding="utf-8-sig", newline="") as h:
                self.assertEqual(len(list(csv.DictReader(h))), 10)

        self.assertEqual(len(found), 210)
        self.assertEqual(len(found), len(set(found)))

    def test_textbook_dskp_anchors_and_backup(self):
        source = ROOT / "rpt_2027" / "psv" / "textbook_dskp_source_map_20261104.json"
        self.assertTrue(source.is_file())
        with source.open(encoding="utf-8") as handle:
            mappings = json.load(handle)["years"]
        self.assertEqual(set(mappings), {"2", "3", "4", "5", "6"})
        for year in YEARS:
            info = mappings[str(year)]
            self.assertEqual(len(info["units"]), 10, f"Tahun {year}: expected 10 textbook units")
            self.assertTrue(info["book"].startswith("https://"))
            self.assertTrue(info["dskp"].startswith("https://"))
            for number in range(1, 43):
                path = ROOT / "rph_standalone" / "psv" / f"year{year}" / f"lesson_{number:03d}.md"
                content = path.read_text(encoding="utf-8")
                self.assertIn(info["book"], content, f"{path}: missing textbook URL")
                self.assertIn(info["dskp"], content, f"{path}: missing DSKP URL")
            backup = ROOT / "rph_standalone" / "psv" / f"year{year}" / "backups_pre90_20261104"
            self.assertEqual(len(list(backup.glob("lesson_???.md"))), 42,
                             f"Tahun {year}: incomplete pre-90 RPH backup")
            landscape = ROOT / "rpt_2027" / "psv" / f"RPT_PSV_Tahun_{year}_2027_DRAF.html"
            self.assertTrue(landscape.is_file())
            self.assertIn("A4 landscape", landscape.read_text(encoding="utf-8"))

    def test_known_printed_dskp_exceptions(self):
        year4 = (ROOT / "rph_standalone" / "psv" / "year4" / "lesson_040.md").read_text(encoding="utf-8")
        self.assertIn("Harum Mewangi", year4)
        self.assertIn("3.1.5", year4)
        year6 = (ROOT / "rph_standalone" / "psv" / "year6" / "lesson_033.md").read_text(encoding="utf-8")
        self.assertIn("**SK:** 3.1", year6)
        self.assertIn("**SP:** 3.2.2", year6)
        year6_project = (ROOT / "rph_standalone" / "psv" / "year6" / "lesson_042.md").read_text(encoding="utf-8")
        self.assertIn("**SP:** 5.1.5", year6_project)

    def test_year6_original_is_backed_up(self):
        backup = ROOT / "rph_standalone" / "psv" / "year6" / "backups_20261104"
        self.assertEqual(len(list(backup.glob("lesson_???.md"))), 42)

if __name__ == "__main__":
    unittest.main()
