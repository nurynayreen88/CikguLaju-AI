import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from web.telegram_verified_rpt_rph_bridge import SourceUnavailable, _resolve_verified_rpt
from web.telegram_verified_sequence_rph_bridge import _available_groups, _unit_catalog
from web_v1_dropdown_catalog import bm_pdp_options, bm_topic_options, bm_unit_options
from web_v1_dropdown_catalog import pdp_options, unit_options


class UnitNavigationTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.db = Path(tmp.name) / "fixture.db"
        with sqlite3.connect(self.db) as conn:
            conn.executescript("""
                CREATE TABLE rpt_entries (
                  id INTEGER, year_label TEXT, subject TEXT, verified INTEGER,
                  notes TEXT, unit_title TEXT, topic TEXT, subtopic TEXT,
                  skill_focus TEXT, sequence_no INTEGER, activity_note TEXT
                );
                CREATE TABLE pi_pdp_details_v2591 (
                  year_label TEXT, pdp_no INTEGER, verified INTEGER, textbook_pages TEXT
                );
                CREATE TABLE rpt_entry_standards (
                  id INTEGER, rpt_entry_id INTEGER, standard_type TEXT,
                  standard_code TEXT, standard_text TEXT, sequence_no INTEGER, verified INTEGER
                );
                CREATE TABLE verified_pdp_sequence (
                  id INTEGER, year_label TEXT, subject TEXT, verification_status TEXT,
                  week_no INTEGER, theme TEXT, unit_code TEXT, unit_title TEXT,
                  pdp_title TEXT, sk_code TEXT, sp_code TEXT, source_sequence_no INTEGER
                );
                INSERT INTO rpt_entries VALUES
                  (1,'Tahun 3','Pendidikan Islam',1,'','','Tilawah','','القرءان 30 مينيت',1,
                   'Murid membaca surah mengikut bacaan guru.'),
                  (2,'Tahun 3','Pendidikan Islam',1,'','','Akidah','','عقيدة 1 جم',2,
                   'Murid memadankan kad mengikut kumpulan.'),
                  (3,'Tahun 3','Pendidikan Islam',1,'','','Jawi','','جاوي 30 مينيت',3,
                   'Murid menulis perkataan pada papan putih.'),
                  (4,'Tahun 3','Pendidikan Islam',1,'','','Jawi','','جاوي 30 مينيت',4,
                   'Aktiviti berpandu, aplikasi dan pentaksiran formatif mengikut SP.');
                INSERT INTO pi_pdp_details_v2591 VALUES
                  ('Tahun 3',1,1,'4'), ('Tahun 3',2,1,'10'), ('Tahun 3',4,1,'12');
                INSERT INTO rpt_entry_standards VALUES
                  (1,1,'SK','1.1','',1,1), (2,1,'SP','1.1.1','',2,1),
                  (3,2,'SK','2.1','',1,1), (4,3,'SK','3.1','',1,1),
                  (5,3,'SP','3.1.1','',2,1), (6,4,'SK','3.1','',1,1),
                  (7,4,'SP','3.1.1','',2,1);
                INSERT INTO verified_pdp_sequence VALUES
                  (1,'Tahun 1','Bahasa Melayu','VERIFIED',1,'Tema 4: Sains','11',
                   'Sains dan Teknologi','Tajuk Satu','1.1','1.1.1',1),
                  (2,'Tahun 1','Bahasa Melayu','VERIFIED',2,'Tema 4: Sains','11',
                   'Sains Dan Teknologi','Tajuk Dua','1.1','1.1.1',2),
                  (3,'Tahun 5','Bahasa Melayu','VERIFIED',1,'TEMA 1 : Keluarga Berwawasan','1',
                   'Masyarakat Penyayang','Bank Rezeki Bergerak','1.1','1.1.1',1),
                  (4,'Tahun 5','Bahasa Melayu','VERIFIED',2,'TEMA 1 : Kemasyarakatan','1',
                   'Masyarakat Penyayang','Projek Alam Sekitar','1.1','1.1.1',2);
            """)

    def test_pi_only_lists_fields_whose_pdp_passes_native_source_validation(self):
        self.assertEqual(unit_options(self.db, 3, "PI"),
                         [{"value": "Al-Quran", "label": "Al-Quran"}])
        lessons = pdp_options(self.db, 3, "PI", "Al-Quran")
        self.assertEqual([row["value"] for row in lessons], ["1"])
        self.assertEqual(lessons[0]["textbook_ref"], "Buku Teks m/s 4")
        runtime = SimpleNamespace(DB_PATH=self.db, CIKGULAJU_DB_V2600_ACTIVE=True)
        selection = {"year": 3, "subject": "PI", "unit": "Al-Quran", "lesson": 1}
        self.assertEqual(_resolve_verified_rpt(runtime, selection)["id"], 1)
        with self.assertRaises(SourceUnavailable):
            _resolve_verified_rpt(runtime, {**selection, "unit": "Jawi"})

    def test_bm_case_variants_share_the_menu_and_keep_the_native_pdp_unit(self):
        theme = "Tema 4: Sains"
        units = bm_unit_options(self.db, 1, theme)
        self.assertEqual(units, [{"value": "Sains dan Teknologi", "label": "Unit 11: Sains dan Teknologi"}])
        topics = bm_topic_options(self.db, 1, theme, units[0]["value"])
        self.assertEqual([item["value"] for item in topics], ["Tajuk Satu", "Tajuk Dua"])
        lessons = bm_pdp_options(self.db, 1, theme, units[0]["value"], "Tajuk Dua")
        self.assertEqual(lessons[0]["origin_unit"], "Sains Dan Teknologi")

    def test_bm_year_five_topic_sits_under_its_textbook_theme(self):
        topics = bm_topic_options(self.db, 5, "Tema 1: Kemasyarakatan", "Masyarakat Penyayang")
        self.assertEqual([item["value"] for item in topics],
                         ["Bank Rezeki Bergerak", "Projek Alam Sekitar"])
        self.assertFalse(bm_unit_options(self.db, 5, "Tema 1: Keluarga Berwawasan"))

    def test_native_sequence_ignores_units_with_no_mapped_pdp(self):
        unit = _unit_catalog([("3.3", "Manusia")])[0]
        incomplete = {"unit_code": "3.3", "unit_title": "Manusia",
                      "pdp_sequence_code": "S3-PDP-020", "sk_code": "3.3", "sp_code": ""}
        self.assertFalse(_available_groups([incomplete], unit, 3, "SCIENCE"))
        complete = {**incomplete, "sp_code": "3.3.1"}
        self.assertEqual(_available_groups([complete], unit, 3, "SCIENCE"),
                         {"S3-PDP-020": [complete]})
