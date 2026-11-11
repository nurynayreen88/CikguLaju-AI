"""Regression: 500 member current capacity; historical 200 migration remains immutable."""
import unittest
from pathlib import Path
from pioneer_percentage import pioneer_percentage
from pioneer_supabase import PIONEER_LIMIT, pioneer_availability


class RakanCap500Tests(unittest.TestCase):
    def test_boundary_and_clamp(self):
        self.assertEqual(PIONEER_LIMIT,500)
        for count,remaining,percent in (
            (0,500,"0.0%"),(1,499,"0.2%"),(7,493,"1.4%"),
            (199,301,"39.8%"),(200,300,"40.0%"),(499,1,"99.8%"),
            (500,0,"100.0%"),(501,0,"100.0%")
        ):
            with self.subTest(count=count):
                self.assertEqual(pioneer_availability(
                    lambda method,path,**kwargs: count),(count,remaining))
                self.assertEqual(pioneer_percentage(count),percent)

    def test_db_migration_updates_both_atomic_paths_without_touching_records(self):
        sql=(Path(__file__).resolve().parents[1]/
             "migrations/20261107_rakan_pembangun_batch1_200_cap.sql"
            ).read_text("utf-8")
        self.assertIn("IF n >= 200 THEN",sql)
        self.assertIn("if v_active_count >= 200 then",sql)
        self.assertIn("199-n",sql)
        self.assertIn("199 - v_active_count",sql)
        self.assertIn("pg_advisory_xact_lock(20261026, 500)",sql)
        self.assertIn("pg_get_functiondef",sql)
        for destructive in ("TRUNCATE ","DELETE FROM ","DROP TABLE ","UPDATE public.pioneer_entitlements"):
            self.assertNotIn(destructive,sql.upper().replace("  "," "))

    def test_telegram_join_closes_when_full(self):
        code=(Path(__file__).resolve().parents[1]/"pioneer_telegram.py"
             ).read_text("utf-8")
        self.assertIn("if remaining == 0:",code)
        self.assertIn("if not pending and pioneer_availability(sb)[1] == 0:",code)
        self.assertIn("Rakan Pembangun sudah penuh",code)


if __name__=="__main__":
    unittest.main()
