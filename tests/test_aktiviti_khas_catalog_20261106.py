"""Quality guards for additive special-activity RPH catalog."""
import json
import unittest
from collections import Counter, defaultdict
from pathlib import Path


CATALOG = Path(__file__).resolve().parents[1] / "rph_standalone" / "aktiviti_khas" / "catalog_v1.json"


class TestAktivitiKhasCatalog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.payload = json.loads(CATALOG.read_text(encoding="utf-8"))
        cls.rows = cls.payload["activities"]

    def test_catalog_count_and_unique_ids(self):
        self.assertEqual(len(self.rows), 50)
        self.assertEqual(len({r["id"] for r in self.rows}), 50)
        self.assertEqual(self.payload["release_status"], "DRAFT_REVIEW")

    def test_phase_and_year_guard(self):
        transisi = [r for r in self.rows if r["category"] == "TRANSISI_TAHUN_1"]
        self.assertEqual(len(transisi), 20)
        self.assertEqual(Counter(r["phase"] for r in transisi),
                         {"Fasa Penyesuaian": 10, "Fasa Kesediaan": 10})
        self.assertTrue(all(r["years"] == [1] for r in transisi))
        self.assertTrue(all(r["sk_sp_status"] == "NOT_APPLICABLE_SPECIAL_ACTIVITY"
                            for r in transisi))

    def test_three_levels_and_ten_distinct_themes(self):
        end = [r for r in self.rows if r["category"] == "SELEPAS_TAMAT_SUKATAN"]
        self.assertEqual(len(end), 30)
        by_level = Counter(tuple(r["years"]) for r in end)
        self.assertEqual(by_level, {(1, 2): 10, (3, 4): 10, (5, 6): 10})
        by_title = defaultdict(list)
        for row in end:
            by_title[row["title"]].append(row)
        self.assertEqual(len(by_title), 10)
        for title, variants in by_title.items():
            with self.subTest(title=title):
                self.assertEqual(len(variants), 3)
                self.assertEqual(len({v["learning_objective"] for v in variants}), 3)
                self.assertEqual({tuple(v["years"]) for v in variants},
                                 {(1, 2), (3, 4), (5, 6)})

    def test_required_rph_fields_and_activities(self):
        for row in self.rows:
            with self.subTest(id=row["id"]):
                for key in ("title", "learning_objective", "set_induksi",
                            "pengukuhan_penilaian", "penutup", "bbm"):
                    self.assertIsInstance(row[key], str)
                    self.assertTrue(row[key].strip())
                self.assertEqual(len(row["aktiviti_utama"]), 3)
                self.assertTrue(all(s.strip() for s in row["aktiviti_utama"]))
                self.assertEqual(len(set(row["aktiviti_utama"])), 3)
                self.assertEqual(row["duration_minutes"], 60)
                self.assertNotIn("lesson", row["id"].lower())

    def test_time_budget(self):
        self.assertEqual(sum(self.payload["rph_minute_plan"].values()), 60)

    def test_non_destructive_lesson_data_policy(self):
        for row in self.rows:
            self.assertNotIn("sk", row)
            self.assertNotIn("sp", row)
            self.assertNotIn("textbook_page", row)
            self.assertNotIn("lesson_number", row)
        self.assertTrue(all(r["sk_sp_status"] == "NOT_ASSIGNED_UNLESS_VERIFIED_TO_SUBJECT"
                            for r in self.rows if r["category"] == "SELEPAS_TAMAT_SUKATAN"))


if __name__ == "__main__":
    unittest.main()
