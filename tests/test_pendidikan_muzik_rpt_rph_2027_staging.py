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
                self.assertRegex(row["rpt2027_slot"]["groupA"], r"^\\d{2}/\\d{2}")
                self.assertRegex(row["rpt2027_slot"]["groupB"], r"^\\d{2}/\\d{2}")
                md = (directory / f"rph_pdp_{i:02d}.md").read_text(encoding="utf-8")
                self.assertIn(row["unit"], md)
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
                    self.assertRegex(sp, r"^[1-5][.][1-9][.]\\d{1,2}$")
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
        self.assertTrue(any("4.1.1" in row["sp"] for row in manifest["pdps"]))
        self.assertTrue(any("3.1.1" in row["sp"] for row in manifest["pdps"]))
        sources = json.loads((MUSIC / "y4_dskp_sp_rph_seeds.json").read_text(encoding="utf-8"))
        self.assertEqual(
            {x["sp"] for x in sources["standards"] if x["flag_kod_sk_sp_tidak_sepadan"]},
            {"3.2.1", "3.2.2", "3.2.3", "4.2.1"},
        )

    def test_year_5_6_risks_remain_visible(self):
        y5 = json.loads((MUSIC / "rpt_rph_2027" / "year5" / "pdp_manifest.json").read_text(encoding="utf-8"))
        y6 = json.loads((MUSIC / "rpt_rph_2027" / "year6" / "pdp_manifest.json").read_text(encoding="utf-8"))
        self.assertTrue(any("belum disahkan" in r["unit"] for r in y5["pdps"]))
        self.assertTrue(any("Baroque" in " ".join(r.get("flags", [])) for r in y6["pdps"]))
        self.assertTrue(any("Classical" in " ".join(r.get("flags", [])) for r in y6["pdps"]))


if __name__ == "__main__":
    unittest.main()
