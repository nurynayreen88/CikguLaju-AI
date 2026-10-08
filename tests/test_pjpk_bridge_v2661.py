"""Non-destructive PJPK bridge checks. Run: python -m unittest discover -s tests -p 'test_pjpk_bridge_v2661.py'"""
import sqlite3
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from pjpk_rpt_bridge_v2659 import enrich_pjpk_rph

class PJPKBridgeTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory()
        self.db = str(Path(self.temp.name) / "pjpk_test.db")
        con = sqlite3.connect(self.db)
        con.executescript("""
            CREATE TABLE rpt_entries (
                id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT, sequence_no INTEGER,
                topic TEXT, unit_title TEXT, verified INTEGER, content_verified INTEGER
            );
            CREATE TABLE rpt_entry_standards (
                id INTEGER PRIMARY KEY, rpt_entry_id INTEGER, standard_type TEXT,
                standard_code TEXT, standard_text TEXT, sequence_no INTEGER, verified INTEGER
            );
            INSERT INTO rpt_entries VALUES (1,'Tahun 2','Pendidikan Jasmani',1,'Teroka Ruang','Pergerakan',1,1);
            INSERT INTO rpt_entries VALUES (2,'Tahun 2','Pendidikan Jasmani',2,'Lari Pantas','Olahraga',1,1);
            INSERT INTO rpt_entries VALUES (3,'Tahun 3','Pendidikan Kesihatan',1,'Jaga Diri','Kesihatan',1,0);
            INSERT INTO rpt_entry_standards VALUES (1,1,'SK','1.1','Pergerakan lokomotor',1,1);
            INSERT INTO rpt_entry_standards VALUES (2,1,'SP','1.1.1','Melakukan pergerakan',2,1);
        """)
        con.close()

    def tearDown(self):
        self.temp.cleanup()

    def connect(self):
        return sqlite3.connect(self.db)

    def test_exact_match_enriches(self):
        x = enrich_pjpk_rph(dict(subject='Pendidikan Jasmani',year='2',sequence_no=1,topic='Teroka Ruang'),self.connect)
        self.assertEqual(x.get('sk_code'),'1.1')
        self.assertEqual(x.get('sp_code'),'1.1.1')
        self.assertTrue(x.get('_pjpk_standards_complete_v2659'))

    def test_wrong_topic_does_not_leak_other_lesson(self):
        x = enrich_pjpk_rph(dict(subject='Pendidikan Jasmani',year='Tahun 2',sequence_no=1,topic='Lari Pantas'),self.connect)
        self.assertNotIn('sp_code',x)

    def test_unverified_content_not_selected(self):
        x = enrich_pjpk_rph(dict(subject='Pendidikan Kesihatan',year='Tahun 3',sequence_no=1,topic='Jaga Diri'),self.connect)
        self.assertNotIn('_pjpk_rpt_source_id_v2659',x)

    def test_unrelated_subject_unchanged(self):
        x = dict(subject='Matematik',year='Tahun 2',topic='Nombor')
        self.assertEqual(enrich_pjpk_rph(x,self.connect),x)

if __name__ == '__main__':
    unittest.main()
