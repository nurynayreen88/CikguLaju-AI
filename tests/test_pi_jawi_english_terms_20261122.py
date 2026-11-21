"""PI-only Jawi teaching terms: exact, safe source-preserving regression."""
from __future__ import annotations
import copy
import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from web.pi_jawi_english_terms_20261122 import (
    _RULES, install, normalize_english_terms, prepare_pi_state,
)

ROOT = Path(__file__).resolve().parents[1]


class TestPITeachingTerms(unittest.TestCase):
    def test_curated_methods_are_jawi_and_idempotent(self):
        examples = {
            "shoulder partner": "راکن سبله",
            "face partner": "راکن برهادڤن",
            "gallery walk": "جلاجه ݢاليري",
            "round robin": "ڤرکوڠسين سچارا برݢيلير",
            "think pair share": "فيکير، برڤاسڠن دان برکوڠسي",
            "(stay &stray)": "(ککل دان ملاوات)",
            "Role-Play (main peranan)": "لاكونن ڤرانن",
            "Personal Learning Experiences (Pengalaman Peribadi)": "ڤڠالمن ڤريبادي",
            "spin –n- think": "ڤوتر دان فيکير",
            "MIX-N-MATCH": "ڤادنکن ڤاسڠن",
            "Roling Chip": "ڤرکوڠسين سچارا برݢيلير",
            "THE YARN YARN": "جالينن بنڠ",
            "Puzzle it Out -selesaikan": "سلسايکن تيکاته-تيکي",
            "I –think": "اي-تينک",
            "brainstorming": "سومبڠ سارن",
            "hot seat": "کروسي ڤانس",
            "TALKING CHIPS": "ݢيليرن برچاکڤ",
            "round table": "ڤربينچڠن ميجا بولت",
            "Recap Group": "اولڠ کاجي برکومڤولن",
            "thumbs up": "ايشارت ايبو جاري",
        }
        for original, jawi in examples.items():
            with self.subTest(source=original):
                corrected = normalize_english_terms("ݢورو مڠݢوناكن (" + original + ").")
                self.assertIn(jawi, corrected)
                self.assertEqual(normalize_english_terms(corrected), corrected)
                self.assertIn("ݢورو مڠݢوناكن", corrected)

    def test_never_rewrite_sk_sp_or_source_master(self):
        original = {
            "subject": "Pendidikan Islam", "task": "rph",
            "lesson": 19, "rpt_entry_id": 1729,
            "rpt_activity_note": "2. موريد (shoulder partner) ممباچ آية",
            "rpt_assessment_note": "KBAT", "sk_text": "1.1 (shoulder partner)",
            "sp_text": "4.1.6 ممڤرينچيكن",
            "_quick_selected_rpt_row_v2388": {"id":1729, "topic":"تيمم", "activity_note":"(shoulder partner)"},
            "quick_rpt_row": {"id":1729, "assessment_note":"round robin"},
            "grouped_sp_texts": ["4.1.6 ممڤرينچيكن"],
        }
        deep = copy.deepcopy(original)
        prepare_pi_state(original)
        self.assertEqual(original["rpt_entry_id"], deep["rpt_entry_id"])
        self.assertEqual(original["sk_text"], deep["sk_text"])
        self.assertEqual(original["sp_text"], deep["sp_text"])
        self.assertEqual(original["grouped_sp_texts"], deep["grouped_sp_texts"])
        self.assertEqual(original["rpt_assessment_note"], "KBAT")
        self.assertIn("راکن سبله", original["rpt_activity_note"])
        self.assertEqual(original["quick_rpt_row"]["id"], 1729)
        self.assertIn("راکن سبله", original["_quick_selected_rpt_row_v2388"]["activity_note"])
        self.assertEqual(deep["_quick_selected_rpt_row_v2388"]["activity_note"], "(shoulder partner)")
        self.assertEqual(deep["quick_rpt_row"]["assessment_note"], "round robin")

    def test_only_pendidikan_islam_and_only_native_rph(self):
        for subject in ("English", "Bahasa Melayu", "Bahasa Arab", "Sains"):
            state = {"subject": subject,"task":"rph","rpt_activity_note":"gallery walk"}
            self.assertIs(prepare_pi_state(state), state)
            self.assertEqual(state["rpt_activity_note"],"gallery walk")
        state={"subject":"Pendidikan Islam","task":"worksheet","rpt_activity_note":"gallery walk"}
        self.assertEqual(prepare_pi_state(state)["rpt_activity_note"],"gallery walk")

    def test_native_telegram_hook_also_serves_web_pdf_and_word(self):
        calls=[]
        def existing(state):
            calls.append(copy.deepcopy(state))
            return "2. موريد (" + state.get("rpt_activity_note","") + ").\nKBAT"
        rt=SimpleNamespace(_local_rph_text=existing)
        self.assertTrue(install(rt))
        self.assertTrue(install(rt))  # no double-wrap
        selected={"subject":"Pendidikan Islam","task":"rph",
                  "rpt_activity_note":"shoulder partner"}
        output=rt._local_rph_text(selected)
        self.assertIn("راکن سبله",output)
        self.assertIn("راکن سبله",selected["rpt_activity_note"])
        self.assertEqual(len(calls),1)
        self.assertEqual(rt._local_rph_text({"subject":"English","task":"rph",
            "rpt_activity_note":"gallery walk"}).count("gallery walk"),1)

    def test_teacher_reflection_standards_and_named_book_stay_exact(self):
        def native(state):
            return (state["rpt_activity_note"] + "\n" + state["sk_text"] +
                    "\n" + state["sp_text"] + "\n" +
                    state["rph_teacher_reflection"] + "\n" + state["book_title"])
        rt=SimpleNamespace(_local_rph_text=native)
        self.assertTrue(install(rt))
        state={
            "subject":"Pendidikan Islam", "task":"rph",
            "rpt_activity_note":"gallery walk",
            "sk_text":"gallery walk dalam petikan asal SK",
            "sp_text":"think pair share dalam petikan SP asal",
            "rph_teacher_reflection":"Saya memilih game untuk refleksi saya.",
            "book_title":"The Gallery Walk (nama rasmi buku)",
        }
        original=copy.deepcopy(state)
        output=rt._local_rph_text(state)
        self.assertIn("جلاجه ݢاليري",output)
        for key in ("sk_text","sp_text","rph_teacher_reflection","book_title"):
            self.assertEqual(state[key],original[key])
            self.assertIn(original[key],output)

    def test_all_809_verified_original_rpt_activities(self):
        db=ROOT/"CikguLaju_Curriculum_Master_v25_93_PI_ENGLISH_Y1_Y4.db"
        pieces=[ROOT/(db.name+x) for x in (".part1",".part2")]
        self.assertTrue(all(p.is_file() for p in pieces))
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/"review.db"
            with path.open("wb") as out:
                for part in pieces:
                    with part.open("rb") as source:
                        while chunk:=source.read(1<<20):
                            out.write(chunk)
            before=hashlib.sha256(path.read_bytes()).hexdigest()
            with sqlite3.connect("file:"+str(path)+"?mode=ro",uri=True) as c:
                c.execute("PRAGMA query_only=ON")
                rows=c.execute("""SELECT year_label,activity_note,assessment_note
                   FROM rpt_entries WHERE subject='Pendidikan Islam'
                     AND verified=1 AND year_label IN
                        ('Tahun 1','Tahun 2','Tahun 3','Tahun 4','Tahun 5','Tahun 6')""").fetchall()
            self.assertEqual(len(rows),809)
            by_year={}
            changed=0
            for year,activity,assessment in rows:
                source=(activity or "")+"\n"+(assessment or "")
                result=normalize_english_terms(source)
                self.assertEqual(result,normalize_english_terms(result))
                self.assertEqual(source.count("\n"),result.count("\n"))
                self.assertEqual(source.count("1."),result.count("1."))
                for pattern,label in _RULES:
                    self.assertIsNone(pattern.search(result),f"English method remains in {year}: {pattern}")
                if result!=source:
                    changed+=1
                    by_year[year]=by_year.get(year,0)+1
            self.assertGreater(changed,300)
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),before)
            print("PI_809_TERMS_QA",{"verified":len(rows),"changed_for_display":changed,
                  "by_year":by_year,"source_db_modified":False})


if __name__=="__main__":
    unittest.main()
