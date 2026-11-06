"""Protect Telegram native verified-RPT source identity and Web access.

Uses a temporary, read-only SQLite master fixture. Never alters production DB.
"""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from flask import Flask
from web.telegram_verified_rpt_rph_bridge import (
    _native_state, _resolve_verified_rpt, SourceUnavailable,
    create_native_db_rph_blueprint,
)


class NativeRPTBridgeTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.db = Path(self.folder.name) / "test_master.db"
        with sqlite3.connect(self.db) as conn:
            conn.execute("""CREATE TABLE rpt_entries (
                id integer primary key, year_label text, subject text,
                verified integer, notes text, unit_title text,
                activity_note text, topic text, subtopic text,
                skill_focus text, sequence_no integer, assessment_note text)""")
            conn.execute("""CREATE TABLE rpt_entry_standards (
                id integer primary key, rpt_entry_id integer,
                standard_type text, standard_code text,
                standard_text text, sequence_no integer, verified integer)""")
            conn.execute("""CREATE TABLE pi_pdp_details_v2591 (
                year_label text, pdp_no integer, verified integer,
                objective_jawi text, textbook_pages text, textbook_unit text)""")
            conn.execute("""INSERT INTO rpt_entries VALUES (
                102,'Tahun 2','Bahasa Melayu',1,'','Unit Bahasa',
                'Guru membimbing murid membaca petikan dan mengenal isi penting. Murid kemudian menulis jawapan berdasarkan bukti teks.',
                'Membaca dan memahami','Isi penting','Membaca',7,'Semak kefahaman murid')""")
            conn.execute("""INSERT INTO rpt_entry_standards VALUES
                (1,102,'SK','2.3','Membaca pelbagai bahan',1,1),
                (2,102,'SP','2.3.1','Membaca memahami petikan',1,1)""")
        self.runtime = Mock()
        self.runtime.DB_PATH = str(self.db)
        self.runtime.CIKGULAJU_DB_V2600_ACTIVE = True
        self.runtime._local_rph_text.return_value = (
            "OBJEKTIF PEMBELAJARAN: Murid membaca petikan dan mengesan isi penting.\n"
            "AKTIVITI UTAMA: Guru membimbing murid mengenal isi utama dalam "
            "petikan pilihan, murid menulis jawapan individu dan menyemak "
            "dengan bukti teks. "*8)
        self.selection = {"year":2,"subject":"BM","unit":"Unit Bahasa","lesson":102}
        self.teacher = {"class":"2 Bestari","date":"2026-11-06",
                        "time":"07:30 - 08:30","students":"31"}

    def test_verified_bm_rpt_is_picked_by_exact_id(self):
        state = _native_state(self.runtime,self.selection,self.teacher)
        self.assertEqual(state["rpt_entry_id"],102)
        self.assertEqual(state["subject"],"Bahasa Melayu")
        self.assertEqual(state["sp_code"],"2.3.1")
        self.assertIn("membaca petikan",state["rpt_activity_note"])
        self.assertEqual(state["rph_class"],"2 Bestari")
        self.assertEqual(state["rph_date"],"06/11/2026")

    def test_wrong_unit_or_subject_never_uses_stale_rpt(self):
        for selection in ({**self.selection,"unit":"Unit Lain"},
                          {**self.selection,"subject":"PI"},
                          {**self.selection,"lesson":103}):
            with self.subTest(selection=selection),self.assertRaises(SourceUnavailable):
                _resolve_verified_rpt(self.runtime,selection)

    def test_disabled_master_rejects_without_fallback(self):
        self.runtime.CIKGULAJU_DB_V2600_ACTIVE = False
        with self.assertRaises(SourceUnavailable):
            _resolve_verified_rpt(self.runtime,self.selection)

    def test_browser_cannot_call_private_endpoint(self):
        app = Flask(__name__)
        app.register_blueprint(create_native_db_rph_blueprint(self.runtime))
        client = app.test_client()
        with patch.dict(os.environ, {
            "CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN":"x"*40,
        }):
            unauth = client.get("/internal/rph/v1/verified-rpt/availability",
                                query_string=self.selection)
            self.assertEqual(unauth.status_code,401)
            auth = client.get("/internal/rph/v1/verified-rpt/availability",
                              headers={"Authorization":"Bearer "+"x"*40},
                              query_string=self.selection)
            self.assertEqual(auth.status_code,200)
            self.assertTrue(auth.get_json()["available"])

    def test_no_standards_means_no_rph(self):
        with sqlite3.connect(self.db) as conn:
            conn.execute("UPDATE rpt_entry_standards SET verified=0 WHERE rpt_entry_id=102")
        with self.assertRaises(SourceUnavailable):
            _resolve_verified_rpt(self.runtime,self.selection)


if __name__=="__main__":
    unittest.main()
