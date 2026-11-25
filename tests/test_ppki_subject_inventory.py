import unittest

from staging.ppki.catalog import SUBJECT, YEARS, options
from staging.ppki.subject_inventory import subject_inventory


class TestPPKISubjectInventory(unittest.TestCase):
    def test_years_subjects_and_legacy_catalog(self):
        for year in YEARS:
            with self.subTest(year=year):
                rows = subject_inventory(year)
                keys = [r["value"] for r in rows]
                self.assertEqual(len(keys), 8 if year <= 3 else 12)
                self.assertEqual(len(keys), len(set(keys)))
                self.assertTrue(all(k.endswith("_PPKI") for k in keys))
                self.assertEqual([r["label"] for r in rows],
                                 sorted((r["label"] for r in rows), key=str.casefold))
                self.assertEqual([r["value"] for r in rows if r["catalog_connected"]], [SUBJECT])
                self.assertEqual([r["value"] for r in options(year)["subjects"]], [SUBJECT])
                self.assertEqual(sum(r["curriculum_group"] == "Asas 3M" for r in rows),
                                 3 if year <= 3 else 0)
                self.assertTrue(all(r["status"] == "pending_source_audit"
                                    for r in rows if r["value"] != SUBJECT))

    def test_invalid_year(self):
        for year in (1, 7, "2", None, True):
            with self.subTest(year=year), self.assertRaises(ValueError):
                subject_inventory(year)
