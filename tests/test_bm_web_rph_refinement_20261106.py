"""BM Web-native source refinement: explicit SP tasks, real line breaks."""
import re
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

from web.bm_web_rph_refinement import (
    _family, refine_web_bm_rows, split_numbered_steps, install,
    complete_verified_bm_standards,
)

SOURCE = "verified_pdp_sequence"


def bm_state(*, details=None, topic="Ceria Pagi"):
    return {
        "subject": "Bahasa Melayu",
        "year": "Tahun 2",
        "pdp_title": topic,
        "textbook_ref": "BT m/s 2–3",
        "_bm_web_native_source": SOURCE,
        "_bm_web_verified_standards": details or (
            {"sp_code": "1.1.1", "sp_text":
             "Mendengar, mengecam, memahami dan menyebut dengan betul"},
        ),
    }


class BMWebQualityTest(unittest.TestCase):
    def test_numbering_starts_at_new_line_but_standards_and_pages_remain(self):
        original = ("1. Guru menunjukkan BT m/s 2–3 dan SP 1.1.1. "
                    "2. Murid mendengar. 3. Guru menilai 3.5 markah. "
                    "Aktiviti 2 – Latihan. 1. Guru menyemak. 2. Murid menjawab.")
        formatted = split_numbered_steps(original)
        self.assertIn("1. Guru menunjukkan BT m/s 2–3 dan SP 1.1.1.\n2. Murid", formatted)
        self.assertIn("\n3. Guru menilai 3.5 markah.", formatted)
        self.assertIn("\nAktiviti 2 – Latihan.\n1. Guru", formatted)
        self.assertIn("\n2. Murid menjawab.", formatted)
        self.assertIn("SP 1.1.1", formatted)
        self.assertIn("3.5", formatted)
        self.assertEqual(formatted, split_numbered_steps(formatted))

    def test_web_bm_generic_becomes_observable_listening_plan(self):
        original = {
            "AKTIVITI UTAMA":
                "Aktiviti 1 – Teroka dengan kad gambar. Guru menyediakan "
                "bahan manipulatif. Aktiviti 2 – Cabaran konteks sebenar.",
            "SET INDUKSI": "1. Guru menunjukkan gambar. 2. Murid menyebut.",
            "PENUTUP": "1. Guru rumus. 2. Murid respon.",
            "STANDARD PEMBELAJARAN": "1.1.1 — Mendengar dan mengecam",
            "STANDARD KANDUNGAN": "1.1",
            "OBJEKTIF PEMBELAJARAN": "Objektif asal",
            "KELAS": "2 Bestari",
        }
        result = refine_web_bm_rows(bm_state(), original)
        self.assertIn("Ceria Pagi", result["AKTIVITI UTAMA"])
        self.assertIn("BT m/s 2–3", result["AKTIVITI UTAMA"])
        self.assertIn("frasa atau ayat", result["AKTIVITI UTAMA"])
        self.assertIn("\n2. ", result["AKTIVITI UTAMA"])
        self.assertIn("\n3. ", result["AKTIVITI UTAMA"])
        self.assertIn("\n2. Murid", result["SET INDUKSI"])
        for k in ("STANDARD KANDUNGAN", "STANDARD PEMBELAJARAN",
                  "OBJEKTIF PEMBELAJARAN", "KELAS"):
            self.assertEqual(result[k], original[k])
        self.assertNotIn("Teroka dengan", result["AKTIVITI UTAMA"])

    def test_non_generic_verified_content_is_not_replaced(self):
        row = {
            "AKTIVITI UTAMA": (
                "1. Guru membaca lima frasa asal daripada petikan Ceria Pagi "
                "berpandukan kad gambar. 2. Murid memadankan gambar dan "
                "menyebut semula frasa."
            ),
            "PENTAKSIRAN": "Senarai semak spesifik asal",
        }
        enriched = refine_web_bm_rows(bm_state(), row)
        self.assertIn("lima frasa asal", enriched["AKTIVITI UTAMA"])
        self.assertIn("\n2. Murid", enriched["AKTIVITI UTAMA"])
        self.assertEqual(row["PENTAKSIRAN"], enriched["PENTAKSIRAN"])

    def test_other_subjects_and_telegram_bm_callbacks_unchanged(self):
        row = {"AKTIVITI UTAMA": "1. Guru mengajar. 2. Murid belajar."}
        for state in (
            {"subject": "Bahasa Melayu", "pdp_title": "Ceria Pagi"},
            {**bm_state(), "subject": "Pendidikan Islam"},
            {**bm_state(), "subject": "Sains"},
        ):
            with self.subTest(state=state["subject"]):
                self.assertIs(refine_web_bm_rows(state, row), row)

    def test_families_are_skill_focused_not_topic_keywords(self):
        examples = {
            "imlak": "Menulis frasa secara imlak.",
            "sunting": "Mengedit dan menyunting pelbagai teks.",
            "mekanis": "Menulis secara mekanis dengan kemas.",
            "menulis": "Menghasilkan perenggan bermakna.",
            "membaca": "Membaca dan meneliti kandungan teks.",
            "mendengar": "Mendengar, mengecam dan memahami ujaran.",
            "bertutur": "Bertutur untuk menyampaikan maklumat.",
            "seni bahasa": "Mendeklamasi sajak dengan sebutan betul.",
            "tatabahasa": "Menggunakan kata nama dalam ayat.",
        }
        for family, phrase in examples.items():
            with self.subTest(family=family):
                self.assertEqual(_family(phrase), family)
        self.assertIsNone(_family("Kefahaman Bahasa"))

    def test_multiple_sp_families_both_represented(self):
        st = bm_state(details=(
            {"sp_code": "1.1.1", "sp_text": "Mendengar dan mengecam frasa."},
            {"sp_code": "1.2.1", "sp_text": "Bertutur dalam situasi tidak formal."},
        ))
        out = refine_web_bm_rows(st, {"AKTIVITI UTAMA": (
            "Aktiviti 1 – Teroka dengan bahan manipulatif."
        )})
        self.assertIn("Guru menyebut frasa", out["AKTIVITI UTAMA"])
        self.assertIn("dialog atau soal jawab", out["AKTIVITI UTAMA"])

    def test_backfill_verified_sp_only_from_exact_bm_year_sk_sp(self):
        with tempfile.TemporaryDirectory() as td:
            db=Path(td)/"curriculum.db"
            with sqlite3.connect(db) as con:
                con.executescript("""CREATE TABLE curriculum_standards(
                   year_label TEXT, subject TEXT, sk_code TEXT, sp_code TEXT,
                   sk_text TEXT, sp_text TEXT, verified INTEGER
                );""")
                rows=[
                    ("Tahun 2","Matematik","1.1","1.1.2","Wrong SK","Wrong math text",1),
                    ("Tahun 3","Bahasa Melayu","1.1","1.1.2","Wrong year","Wrong year BM",1),
                    ("Tahun 2","Bahasa Melayu","1.1","1.1.2","BM SK","Mendengar dan memberikan respons terhadap soalan, suruhan, pesanan dan permintaan.",1),
                    ("Tahun 2","Bahasa Melayu","1.1","1.1.3","Other","Unverified SP",0),
                ]
                con.executemany("INSERT INTO curriculum_standards VALUES (?,?,?,?,?,?,?)",rows)
            source=({"sk_code":"1.1","sp_code":"1.1.2","sp_text":"","sk_text":""},)
            got=complete_verified_bm_standards(db,2,source)
            self.assertEqual(got[0]["sp_text"],rows[2][5])
            self.assertEqual(got[0]["sk_text"],"BM SK")
            self.assertEqual(source[0]["sp_text"],"")
            self.assertEqual(complete_verified_bm_standards(
                db,2,({"sk_code":"1.1","sp_code":"1.1.3","sp_text":""},)
            )[0]["sp_text"],"")

    def test_genuine_bm_sp_semantics_are_expressed_in_refined_activities(self):
        cases=(
            ({"sp_code":"1.1.2","sp_text":"Mendengar, memahami dan memberikan respons terhadap soalan, suruhan, pesanan dan permintaan"},
             "Kenali Rakan", ("soalan","suruhan","pesanan","permintaan")),
            ({"sp_code":"1.1.1","sp_text":"Mendengar dan mengecam sebutan ayat tunggal dan ayat majmuk"},
             "Suria Pagi", ("ayat tunggal","ayat majmuk")),
            ({"sp_code":"4.1.1","sp_text":"Bercerita dan mengujarkan dialog yang mengandungi peribahasa"},
             "Program Kebun Komuniti", ("peribahasa","dialog")),
        )
        for sp,topic,markers in cases:
            with self.subTest(topic=topic):
                state=bm_state(details=(sp,),topic=topic)
                result=refine_web_bm_rows(state,{
                    "AKTIVITI UTAMA":"Aktiviti 1  Dengar untuk Maklumat (12 minit) "
                                    "Aktiviti 2  Latihan Kreatif (15 minit).",
                })
                for marker in markers:
                    self.assertIn(marker,result["AKTIVITI UTAMA"].lower())
                self.assertIn(topic,result["AKTIVITI UTAMA"])
                self.assertIn("\n2. ",result["AKTIVITI UTAMA"])
                self.assertIn("\n3. ",result["AKTIVITI UTAMA"])

    def test_idempotent_installer_preserves_original_renderer(self):
        def previous(state, *_):
            return {"AKTIVITI UTAMA": "1. Guru mula. 2. Murid ikut.",
                    "STANDARD PEMBELAJARAN": "1.1.1"}
        runtime = SimpleNamespace(_rph_rows=previous)
        self.assertTrue(install(runtime))
        self.assertTrue(install(runtime))
        self.assertEqual(runtime._rph_rows({}, ""), previous({}, ""))
        self.assertEqual(runtime._rph_rows(bm_state(), "")["AKTIVITI UTAMA"],
                         "1. Guru mula.\n2. Murid ikut.")

    def test_no_false_textbook_claim_without_source_page(self):
        st = bm_state()
        st["textbook_ref"] = ""
        result = refine_web_bm_rows(st, {"AKTIVITI UTAMA":
            "Aktiviti 1 – Teroka dengan kad gambar."})
        self.assertNotIn("BT m/s", result["AKTIVITI UTAMA"])


if __name__ == "__main__":
    unittest.main()
