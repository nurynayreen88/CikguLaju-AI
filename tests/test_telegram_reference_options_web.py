"""Only verified per-PdP textbook pages may be shown in Web dropdowns."""
import os
import sqlite3
import tempfile
import unittest
from web_v1_dropdown_catalog import pdp_options


class VerifiedPIPagesTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "master.db")
        with sqlite3.connect(self.db) as conn:
            conn.execute("""CREATE TABLE rpt_entries(
                id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                sequence_no INTEGER, unit_title TEXT, topic TEXT, subtopic TEXT,
                skill_focus TEXT, verified INTEGER, notes TEXT
            )""")
            conn.executemany(
                "INSERT INTO rpt_entries VALUES(?,?,?,?,?,?,?,?,?,?)", [
                    (10, "Tahun 3", "Pendidikan Islam", 1, "Bidang Al-Quran",
                     "Bacaan", "Surah al-Fatihah", "", 1, ""),
                    (11, "Tahun 3", "Pendidikan Islam", 2, "Bidang Al-Quran",
                     "Bacaan", "Hafazan", "", 1, ""),
                    (12, "Tahun 3", "Pendidikan Islam", 3, "Bidang Al-Quran",
                     "Bacaan", "Tajwid", "", 1, ""),
                ])
            conn.execute("""CREATE TABLE pi_pdp_details_v2591(
                year_label TEXT, pdp_no INTEGER, textbook_pages TEXT,
                verified INTEGER)""")
            conn.executemany(
                "INSERT INTO pi_pdp_details_v2591 VALUES(?,?,?,?)", [
                    ("Tahun 3", 1, "13–14", 1),
                    ("Tahun 3", 2, "16", 0),
                    ("Tahun 3", 3, "30", 1),
                    ("Tahun 3", 3, "31", 1),
                ])

    def tearDown(self):
        self.tmp.cleanup()

    def test_only_unambiguous_verified_page_refs(self):
        rows = pdp_options(self.db, 3, "PI", "Bidang Al-Quran")
        self.assertEqual([r["value"] for r in rows], ["10", "11", "12"])
        self.assertEqual(rows[0]["textbook_ref"], "Buku Teks m/s 13–14")
        self.assertNotIn("textbook_ref", rows[1])
        self.assertNotIn("textbook_ref", rows[2])

    def test_absent_source_table_keeps_legacy_options(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute("DROP TABLE pi_pdp_details_v2591")
        rows = pdp_options(self.db, 3, "PI", "Bidang Al-Quran")
        self.assertEqual(len(rows), 3)
        self.assertTrue(all("textbook_ref" not in r for r in rows))


if __name__ == "__main__":
    unittest.main()
