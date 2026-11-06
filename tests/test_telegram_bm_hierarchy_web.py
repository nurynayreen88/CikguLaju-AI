"""BM Web dropdowns must use Telegram's verified_pdp_sequence, not skill RPT."""
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask

from web_v1_dropdown_catalog import (
    display_unit_label, bm_theme_options, bm_unit_options,
    bm_topic_options, bm_pdp_options, bm_sequence_token,
)
from web.telegram_curriculum_api import create_curriculum_blueprint


def seed_native_bm(db):
    with sqlite3.connect(db) as con:
        con.execute("""CREATE TABLE verified_pdp_sequence(
            id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
            week_no INTEGER, theme TEXT, unit_code TEXT, unit_title TEXT,
            pdp_title TEXT, sk_code TEXT, sp_code TEXT,
            verification_status TEXT, textbook_ref TEXT,
            activitybook_ref TEXT, skill_metadata TEXT,
            source_sequence_no INTEGER)""")
        con.executemany(
            """INSERT INTO verified_pdp_sequence VALUES
                (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""", [
                (1, "Tahun 2", "Bahasa Melayu", 2,
                 "Kekeluargaan", "1", "Keluargaku Sayang", "Ceria Pagi",
                 "1.1", "1.1.1", "VERIFIED", "BT m/s 2–3", "BA m/s 1", "", 1),
                (2, "Tahun 2", "Bahasa Melayu", 2,
                 "Kekeluargaan", "1", "Keluargaku Sayang", "Ceria Pagi",
                 "1.2", "1.2.1", "VERIFIED", "BT m/s 2–3", "BA m/s 1", "", 1),
                (3, "Tahun 2", "Bahasa Melayu", 2,
                 "Kekeluargaan", "1", "Keluargaku Sayang", "Baca bersama",
                 "2.1", "2.1.1", "VERIFIED", "BT m/s 4", "BA m/s 2", "", 2),
                (4, "Tahun 2", "Bahasa Melayu", 2,
                 "Kekeluargaan", "2.0", "Kemahiran Membaca", "Membaca",
                 "2.1", "2.1.1", "VERIFIED", "", "", "", 3),
                (5, "Tahun 2", "Bahasa Melayu", 3,
                 "Kekeluargaan", "2", "Jiran Sepakat", "Hormati Jiran",
                 "2.1", "2.1.1", "REJECT_NON_SK", "", "", "", 4),
                (6, "Tahun 2", "Bahasa Melayu", 4,
                 "Perpaduan", "3", "Jiran Baik", "Bermain",
                 "", "", "VERIFIED", "", "", "", 5),
            ])
        # Synthetic RPT skill domains must be entirely ignored.
        con.execute("""CREATE TABLE rpt_entries(
            id INTEGER, year_label TEXT, subject TEXT, sequence_no INTEGER,
            theme TEXT, unit_code TEXT, unit_title TEXT,
            topic TEXT, subtopic TEXT, skill_focus TEXT,
            verified INTEGER,notes TEXT)""")
        con.execute("""INSERT INTO rpt_entries VALUES
            (80,'Tahun 2','Bahasa Melayu',1,'', '1.0',
             'Kemahiran Mendengar dan Bertutur','Mendengar','','',1,'')""")


class BMHierarchyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "master.db")
        seed_native_bm(self.db)
        app = Flask(__name__)
        app.register_blueprint(create_curriculum_blueprint(lambda: self.db))
        self.client = app.test_client()
        self.env = {"CIKGULAJU_CURRICULUM_API_ENABLED":"1",
                    "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"t"*40}
        self.headers = {"Authorization":"Bearer "+"t"*40}

    def tearDown(self):
        self.tmp.cleanup()

    def test_true_telegram_source_and_shared_sksp_group(self):
        themes = bm_theme_options(self.db, 2)
        self.assertEqual(themes[0]["value"], "Kekeluargaan")
        self.assertEqual(
            bm_unit_options(self.db, 2, "Kekeluargaan"),
            [{"value":"Keluargaku Sayang","label":"Unit 1: Keluargaku Sayang"}])
        self.assertEqual(
            bm_topic_options(self.db, 2, "Kekeluargaan", "Keluargaku Sayang"),
            [{"value":"Ceria Pagi","label":"Ceria Pagi"},
             {"value":"Baca bersama","label":"Baca bersama"}])
        pdp = bm_pdp_options(self.db, 2, "Kekeluargaan",
                             "Keluargaku Sayang", "Ceria Pagi")
        self.assertEqual(len(pdp), 1)  # two SPs in one real PdP
        self.assertEqual(pdp[0]["value"], bm_sequence_token(
            2, "Kekeluargaan", "1", "Keluargaku Sayang", "Ceria Pagi"))
        self.assertEqual(pdp[0]["textbook_ref"], "BT m/s 2–3")
        self.assertEqual(pdp[0]["pdp_no"], 1)
        self.assertFalse(bm_pdp_options(
            self.db, 2, "Kekeluargaan", "Kemahiran Membaca", "Membaca"))
        self.assertFalse(bm_pdp_options(
            self.db, 2, "Perpaduan", "Jiran Baik", "Bermain"))

    def test_source_unit_number_not_guessed(self):
        self.assertEqual(display_unit_label("Masa dan Waktu", ""),
                         "Masa dan Waktu")
        self.assertEqual(display_unit_label("Unit 03 — Keluarga", ""),
                         "Unit 3: Keluarga")
        self.assertEqual(display_unit_label("Jom Membaca", "U2"),
                         "Unit 2: Jom Membaca")

    def test_private_api_resolves_opaque_pdp(self):
        with patch.dict(os.environ, self.env):
            url="/internal/curriculum/v1/bm-themes?year=2&subject=BM"
            self.assertEqual(self.client.get(url).status_code, 401)
            self.assertEqual(self.client.get(url,headers=self.headers).status_code,200)
            r=self.client.get(
                "/internal/curriculum/v1/bm-pdp?year=2&subject=BM"
                "&theme=Kekeluargaan&unit=Keluargaku%20Sayang"
                "&topic=Ceria%20Pagi",headers=self.headers)
            self.assertEqual(r.status_code,200,r.json)
            self.assertEqual(len(r.json["items"]),1)
            self.assertTrue(r.json["items"][0]["value"].startswith("b"))
            self.assertEqual(self.client.get(
                url+"&extra=bad",headers=self.headers).status_code,400)


if __name__ == "__main__":
    unittest.main()
