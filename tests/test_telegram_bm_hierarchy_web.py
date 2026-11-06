"""Regression: BM Web must not expose synthetic SK/SP skills as book units."""
import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch
from flask import Flask
from web_v1_dropdown_catalog import (
    display_unit_label, bm_theme_options, bm_unit_options, bm_topic_options,
    bm_pdp_options,
)
from web.telegram_curriculum_api import create_curriculum_blueprint


class BMHierarchyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.db = os.path.join(self.tmp.name, "master.db")
        with sqlite3.connect(self.db) as con:
            con.execute("""CREATE TABLE rpt_entries(
                id INTEGER PRIMARY KEY, year_label TEXT, subject TEXT,
                sequence_no INTEGER, theme TEXT, unit_code TEXT,
                unit_title TEXT, topic TEXT, subtopic TEXT, skill_focus TEXT,
                verified INTEGER, notes TEXT)""")
            con.execute("""CREATE TABLE textbook_page_lesson_map(
                year_label TEXT, subject TEXT, verified INTEGER,
                unit_title TEXT, lesson_no TEXT, content_topic TEXT,
                book_title TEXT, page_start INTEGER, page_end INTEGER)""")
            con.executemany(
                "INSERT INTO rpt_entries VALUES(?,?,?,?,?,?,?,?,?,?,?,?)", [
                    (1, "Tahun 2", "Bahasa Melayu", 1, "Tema 1: Kekeluargaan",
                     "U1", "Keluargaku Sayang", "Ceria Pagi", "Dengar dan jawab",
                     "Mendengar", 1, ""),
                    (2, "Tahun 2", "Bahasa Melayu", 2, "Tema 1: Kekeluargaan",
                     "U1", "Keluargaku Sayang", "Ceria Pagi", "Baca teks",
                     "Membaca", 1, ""),
                    (3, "Tahun 2", "Bahasa Melayu", 3, "",
                     "1.0", "Kemahiran Mendengar dan Bertutur", "Kemahiran",
                     "", "Mendengar", 1, ""),
                    (4, "Tahun 2", "Bahasa Melayu", 4, "Tema 2",
                     "2.0", "Kemahiran Membaca", "Membaca",
                     "", "Membaca", 1, ""),
                    (5, "Tahun 2", "Bahasa Melayu", 5, "Tema 2",
                     "U2", "Jiran Sepakat", "Hormati Jiran",
                     "", "", 0, ""),
                    (6, "Tahun 2", "Bahasa Melayu", 6, "Tema 2",
                     "U2", "Jiran Sepakat", "Hormati Jiran",
                     "", "", 1, "superseded"),
                ])
            con.executemany(
                "INSERT INTO textbook_page_lesson_map VALUES(?,?,?,?,?,?,?,?,?)", [
                    ("Tahun 2", "Bahasa Melayu", 1, "Keluargaku Sayang", "1",
                     "Ceria Pagi", "Buku Teks BM", 2, 3),
                    ("Tahun 2", "Bahasa Melayu", 1, "Keluargaku Sayang", "2",
                     "Ceria Pagi", "Buku Teks BM", 4, 4),
                    ("Tahun 2", "Bahasa Melayu", 1, "Keluargaku Sayang", "2",
                     "Unrelated", "Buku Teks BM", 99, 99),
                ])
        self.app = Flask(__name__)
        self.app.register_blueprint(create_curriculum_blueprint(lambda: self.db))
        self.client = self.app.test_client()
        self.env = {"CIKGULAJU_CURRICULUM_API_ENABLED": "1",
                    "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "t" * 40}
        self.headers = {"Authorization": "Bearer " + "t" * 40}

    def tearDown(self):
        self.tmp.cleanup()

    def test_real_telegram_structure_and_pages(self):
        self.assertEqual(bm_theme_options(self.db, 2),
                         [{"value": "Tema 1: Kekeluargaan",
                           "label": "Tema 1: Kekeluargaan"}])
        self.assertEqual(bm_unit_options(self.db, 2, "Tema 1: Kekeluargaan"),
                         [{"value": "Keluargaku Sayang",
                           "label": "Unit 1: Keluargaku Sayang"}])
        self.assertEqual(bm_topic_options(
            self.db, 2, "Tema 1: Kekeluargaan", "Keluargaku Sayang"),
            [{"value": "Ceria Pagi", "label": "Ceria Pagi"}])
        pdp = bm_pdp_options(
            self.db, 2, "Tema 1: Kekeluargaan",
            "Keluargaku Sayang", "Ceria Pagi")
        self.assertEqual([r["value"] for r in pdp], ["1", "2"])
        self.assertEqual([r["textbook_ref"] for r in pdp],
                         ["Buku Teks m/s 2–3", "Buku Teks m/s 4"])
        self.assertTrue(pdp[0]["label"].startswith("PdP 001"))
        self.assertFalse(bm_pdp_options(
            self.db, 2, "Tema 2", "Kemahiran Membaca", "Membaca"))

    def test_never_invent_missing_unit_number(self):
        self.assertEqual(display_unit_label("Masa dan Waktu", ""),
                         "Masa dan Waktu")
        self.assertEqual(display_unit_label("Unit 03 — Keluarga", ""),
                         "Unit 3: Keluarga")
        self.assertEqual(display_unit_label("Jom Membaca", "U2"),
                         "Unit 2: Jom Membaca")

    def test_private_http_fails_closed_and_keeps_exact_row_id(self):
        with patch.dict(os.environ, self.env):
            url = "/internal/curriculum/v1/bm-themes?year=2&subject=BM"
            self.assertEqual(self.client.get(url).status_code, 401)
            res = self.client.get(url, headers=self.headers)
            self.assertEqual(res.status_code, 200)
            self.assertEqual(res.get_json()["source"], "telegram-runtime-v1")
            r = self.client.get(
                "/internal/curriculum/v1/bm-pdp?year=2&subject=BM"
                "&theme=Tema%201%3A%20Kekeluargaan"
                "&unit=Keluargaku%20Sayang&topic=Ceria%20Pagi",
                headers=self.headers,
            )
            self.assertEqual(r.status_code, 200)
            self.assertEqual([x["value"] for x in r.get_json()["items"]],
                             ["1", "2"])
            self.assertEqual(self.client.get(
                url + "&unexpected=1", headers=self.headers
            ).status_code, 400)


if __name__ == "__main__":
    unittest.main()
