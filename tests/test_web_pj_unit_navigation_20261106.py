"""PJ Web: one true textbook Unit, activity-level numbered PdP, no PK changes."""
import unittest

from web.unified_rph_web import (
    PJ_TEXTBOOK_UNIT_SEGMENTS, source_records, unit_options, pdp_options,
    verified_preview,
)


class PJCanonicalUnitTests(unittest.TestCase):
    def test_all_five_years_have_unique_numbered_textbook_units(self):
        expected = {
            2: (37, [1, 2, 3, 4, 6, 7, 8]),
            3: (38, list(range(1, 11))),
            4: (34, list(range(1, 10))),
            5: (33, [1, 2, 3, 4, 5, 6, 8, 9, 10]),
            6: (34, [1, 2, 3, 4, 5, 6, 8, 9, 10]),
        }
        for year, (count, numbers) in expected.items():
            with self.subTest(year=year):
                rows = source_records(year, "PJPK", "PJ")
                self.assertEqual(len(rows), count)
                self.assertEqual([r["lesson"] for r in rows], list(range(1, count+1)))
                self.assertEqual(len({r["token"] for r in rows}), count)
                options = unit_options(year, "PJPK", "PJ")
                self.assertEqual(len(options), len(numbers))
                self.assertEqual(
                    [int(x["value"].split(":")[0].split(" ")[1]) for x in options],
                    numbers)
                self.assertEqual(len({o["value"] for o in options}), len(options))
                self.assertTrue(all(o["value"] == o["label"] and
                                    o["label"].startswith("Unit ") for o in options))
                assembled = []
                for option in options:
                    pdps = pdp_options(year, "PJPK", option["value"], "PJ")
                    self.assertTrue(pdps)
                    self.assertTrue(all(x["label"].startswith("PdP ") for x in pdps))
                    self.assertTrue(all(" UNIT " not in x["label"].upper() for x in pdps
                                        if "TAJUK" in x["label"].upper()))
                    assembled.extend(x["value"] for x in pdps)
                self.assertEqual(assembled, [r["token"] for r in rows])

    def test_year_5_unit_1_appears_once_with_eight_distinct_pdps(self):
        u = "Unit 1: Jadi Yang Terbaik"
        options = unit_options(5, "PJPK", "PJ")
        self.assertEqual(sum(x["value"] == u for x in options), 1)
        pdps = pdp_options(5, "PJPK", u, "PJ")
        self.assertEqual(len(pdps), 8)
        self.assertEqual(pdps[0]["label"], "PdP 001 — MENGIMBANG")
        self.assertEqual(pdps[1]["label"], "PdP 002 — BINAAN HEBAT")
        self.assertEqual(pdps[7]["value"], "p-5-PJ-008")
        self.assertFalse(pdp_options(5, "PJPK", "UNIT 1: JADI YANG TERBAIK TAJUK: MENGIMBANG", "PJ"))

    def test_bare_titles_follow_the_correct_printed_unit(self):
        examples = (
            (2, 28, "Unit 6: Santai Ria", "Jalan-Jalan Cari Harta"),
            (3, 7, "Unit 3: Serang Sampai Menang", "Hantaran Pantas Elak Dipintas"),
            (4, 9, "Unit 3: Johan Kategori Serangan", "JAUH DAN DEKAT"),
            (5, 13, "Unit 3: Serang Menang", "KELECEK BERBISA"),
            (6, 29, "Unit 9: Konsep Kecergasan", "KEKAL CERGAS"),
        )
        for year, no, unit, activity in examples:
            with self.subTest(year=year, pdp=no):
                rec = source_records(year, "PJPK", "PJ")[no-1]
                self.assertEqual(rec["unit"], unit)
                self.assertEqual(rec["label"], f"PdP {no:03d} — {activity}")
                self.assertEqual(rec["token"], f"p-{year}-PJ-{no:03d}")
                self.assertIsNone(verified_preview(year, "PJPK", "Wrong unit", rec["token"], "PJ"))

    def test_pk_is_unchanged_and_separate(self):
        for year in range(2, 7):
            with self.subTest(year=year):
                records = source_records(year, "PJPK", "PK")
                self.assertTrue(records)
                self.assertTrue(all(r["token"].startswith(f"p-{year}-PK-") for r in records))
                self.assertEqual(unit_options(year, "PJPK", "PK"),
                                 [{"value": name, "label": name}
                                  for name in dict.fromkeys(r["unit"] for r in records)])
                self.assertTrue(all(not r["unit"].startswith("Unit ") for r in records))

    def test_static_coverage_is_monotonic_and_matches_release_manifest(self):
        for year, segments in PJ_TEXTBOOK_UNIT_SEGMENTS.items():
            self.assertTrue(all(segments[i][0] < segments[i+1][0]
                                for i in range(len(segments)-1)))
            self.assertEqual(segments[-1][0],
                             {2: 37, 3: 38, 4: 34, 5: 33, 6: 34}[year])


if __name__ == "__main__":
    unittest.main()
