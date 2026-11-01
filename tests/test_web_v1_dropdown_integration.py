"""Integration tests using a disposable SQLite RPT fixture, never production data."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from web_v1_dropdown_catalog import available_subject_options, unit_options, pdp_options


class DropdownIntegrationTests(unittest.TestCase):
    def test_full_year_subject_unit_pdp_navigation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "rpt.db"
            with sqlite3.connect(path) as con:
                con.execute("""CREATE TABLE rpt_entries (
                    id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                    verified INTEGER, notes TEXT, sequence_no INTEGER,
                    unit_title TEXT, topic TEXT, subtopic TEXT, skill_focus TEXT)""")
                con.executemany("""INSERT INTO rpt_entries
                    (id,year_label,subject,verified,notes,sequence_no,unit_title,topic,subtopic,skill_focus)
                    VALUES (?,?,?,?,?,?,?,?,?,?)""", [
                    (1,"Tahun 3","Bahasa Inggeris",1,"",1,"Welcome","Greetings","Hello","Speaking"),
                    (2,"Tahun 3","Bahasa Inggeris",1,"",2,"Welcome","Greetings","Names","Listening"),
                    (3,"Tahun 3","Bahasa Inggeris",1,"",3,"Animals","Pets","Cats","Reading"),
                    (4,"Tahun 3","Bahasa Inggeris",0,"",4,"Hidden","Old","Old",""),
                    (5,"Tahun 3","Sains",1,"superseded",5,"Hidden","Old","Old",""),
                    (6,"Tahun 4","Bahasa Melayu",1,"",1,"Other","Other","Other",""),
                ])
            self.assertEqual([x["value"] for x in available_subject_options(path, 3)], ["ENGLISH"])
            self.assertEqual([x["value"] for x in unit_options(path, 3, "ENGLISH")], ["Welcome", "Animals"])
            result = pdp_options(path, 3, "ENGLISH", "Welcome")
            self.assertEqual([x["value"] for x in result], ["1", "2"])
            self.assertTrue(all(x["standalone_rph_verified"] is False for x in result))
            self.assertEqual(pdp_options(path, 3, "ENGLISH", "Hidden"), [])
            self.assertEqual([x["value"] for x in available_subject_options(path, 4)], ["BM"])
            with sqlite3.connect(path) as con:
                self.assertEqual(con.execute("SELECT COUNT(*) FROM rpt_entries").fetchone()[0], 6)


if __name__ == "__main__":
    unittest.main()
