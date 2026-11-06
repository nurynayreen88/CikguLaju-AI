"""Regression: single batch-1 capacity shared by UI, backend and Supabase."""
import unittest
from pathlib import Path
from pioneer_percentage import pioneer_percentage
from pioneer_supabase import PIONEER_LIMIT, pioneer_availability


class RakanCap200Tests(unittest.TestCase):
    def test_boundary_and_clamp(self):
        self.assertEqual(PIONEER_LIMIT,200)
        for count,remaining,percent in (
            (0,200,"0.0%"),(1,199,"0.5%"),(7,193,"3.5%"),
            (199,1,"99.5%"),(200,0,"100.0%"),(201,0,"100.0%")
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
        self.assertIn("Rakan Pembangun batch pertama sudah penuh",code)


if __name__=="__main__":
    unittest.main()
