"""All nine English Year 5 teacher-choice RPH suggestions: native Word/PDF tests.

This suite doesn't import app.py, contact teachers, modify credits, or label
the proposed projects official/READY. Source file and SOW gates are read only.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import types
import unittest

from web.english_y5_teacher_choice_runtime import (
    PROPOSAL_PATH, PROJECTS, VERSION, adapt_rows, install, load_proposal, _data
)
from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS, LESSON_ROOT, approved_for_telegram,
)

ROOT = Path(__file__).resolve().parents[1]
OLD = {
    "TAJUK":"Legacy RPH",
    "TARIKH":"04/11/2026",
    "MASA":"09:30",
    "KELAS":"5 Maju",
    "BILANGAN MURID":"30",
    "REFLEKSI":"Teacher reflection",
    "MAIN CONTENT STANDARD":"LEGACY WRONG CS",
    "MAIN LEARNING STANDARD":"LEGACY WRONG LS",
    "COMPLEMENTARY CONTENT STANDARD":"LEGACY WRONG CS",
    "COMPLEMENTARY LEARNING STANDARD":"LEGACY WRONG LS",
    "AKTIVITI UTAMA":"Generic RPH activities",
}


class Year5NineTeacherChoiceProposals(unittest.TestCase):
    def test_nine_proposals_60_minutes_each_and_source_gated(self):
        data = _data()
        self.assertEqual(set(data), {str(n) for n in CHOICE_LESSONS})
        self.assertEqual(len(data), 9)
        for number in sorted(CHOICE_LESSONS):
            with self.subTest(lesson=number):
                candidate = load_proposal(number)
                self.assertIsNotNone(candidate)
                self.assertEqual(
                    sum(x["minutes"] for x in candidate["phases"]) +
                    candidate["pbd"]["minutes"] + candidate["closure"]["minutes"], 60)
                self.assertEqual(candidate["phases"][0]["label"], "Set Induction")
                self.assertGreaterEqual(len(candidate["phases"]), 3)
                for phase in candidate["phases"]:
                    self.assertTrue(phase["teacher"].strip())
                    self.assertTrue(phase["pupils"].strip())
                self.assertTrue(candidate["pbd"]["teacher"])
                self.assertTrue(candidate["pbd"]["pupils"])
                self.assertTrue(candidate["criteria"])
                self.assertTrue(candidate["materials"])
                self.assertTrue(candidate["differentiation"])
                self.assertFalse(approved_for_telegram(number))
                if number in PROJECTS:
                    self.assertIn("Project-Based Learning", candidate["kind"])
                else:
                    self.assertIn("Language Awareness", candidate["kind"])

    def test_document_rows_use_actual_proposal_and_pbd(self):
        for number in sorted(CHOICE_LESSONS):
            state = {"subject":"English", "year":"Tahun 5",
                     "lesson_no":number, "task":"rph"}
            with self.subTest(lesson=number):
                old = dict(OLD)
                out = adapt_rows(state, old)
                self.assertIsNot(out, old)
                self.assertEqual(old, OLD)
                self.assertIn("CADANGAN CIKGULAJU (DRAF)", out["TAJUK"])
                self.assertNotIn("LEGACY", out["MAIN LEARNING STANDARD"])
                self.assertIn("not fixed by SOW", out["MAIN LEARNING STANDARD"])
                self.assertIn("not fixed by SOW", out["COMPLEMENTARY LEARNING STANDARD"])
                self.assertIn("Teacher:", out["SET INDUKSI"])
                self.assertIn("Pupils:", out["SET INDUKSI"])
                self.assertIn("Teacher:", out["AKTIVITI UTAMA"])
                self.assertIn("Pupils:", out["AKTIVITI UTAMA"])
                self.assertIn("Teacher:", out["PENTAKSIRAN"])
                self.assertIn("Pupils:", out["PENTAKSIRAN"])
                self.assertIn("Teacher:", out["PENUTUP"])
                self.assertIn("Pupils:", out["PENUTUP"])
                self.assertNotIn("Generic RPH", out["AKTIVITI UTAMA"])
                self.assertNotIn("QA:", "\n".join(str(v) for v in out.values()))
                self.assertNotIn("_DRAFT.md", "\n".join(str(v) for v in out.values()))
                for field in ("TARIKH","MASA","KELAS","BILANGAN MURID","REFLEKSI"):
                    self.assertEqual(out[field], OLD[field])
                self.assertNotRegex(out["MAIN LEARNING STANDARD"], r"\d\.\d\.\d")

    def test_language_awareness_not_mislabeled_as_project(self):
        for number in CHOICE_LESSONS - PROJECTS:
            p = load_proposal(number)
            self.assertIn("SB p.", p["materials"])
            self.assertIn("TB p.", p["materials"])
            self.assertNotIn("CikguLaju Project Proposal", p["topic"])
        for number in PROJECTS:
            p = load_proposal(number)
            self.assertIn("CikguLaju Project Proposal", p["topic"])
            self.assertIn("no mandatory SB/WB/audio", p["materials"])

    def test_l88_and_l160_have_distinct_projects(self):
        out88 = adapt_rows({"year":"Year 5","subject":"English","lesson_no":88}, OLD)
        out160 = adapt_rows({"year":"Year 5","subject":"English","lesson_no":160}, OLD)
        self.assertIn("Dream School Day", out88["TAJUK"])
        self.assertIn("Eco-Holiday Brochure", out160["TAJUK"])
        self.assertIn("timetable", out88["AKTIVITI UTAMA"])
        self.assertIn("brochure", out160["AKTIVITI UTAMA"])
        self.assertNotEqual(out88["AKTIVITI UTAMA"], out160["AKTIVITI UTAMA"])

    def test_fixed_151_and_other_years_subjects_untouched(self):
        for state in (
            {"year":"Year 5","subject":"English","lesson_no":1},
            {"year":"Year 5","subject":"English","lesson_no":141},
            {"year":"Year 5","subject":"English","lesson_no":159},
            {"year":"Year 4","subject":"English","lesson_no":88},
            {"year":"Year 6","subject":"English","lesson_no":88},
            {"year":"Year 1","subject":"English","lesson_no":88},
            {"year":"Year 5","subject":"Matematik","lesson_no":88},
            {"year":"Year 5","subject":"English","lesson_no":88,"task":"worksheet"},
            {"year":"Year 5","subject":"English","lesson_no":"../88"},
            {"year":"Year 5","subject":"English","lesson_no":True},
            {"year":"Year 5","subject":"English","lesson_no":161},
        ):
            with self.subTest(state=state):
                self.assertIs(adapt_rows(state, OLD), OLD)

    def test_modified_proposal_or_missing_source_fail_closed(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            data = json.loads(PROPOSAL_PATH.read_text(encoding="utf-8"))
            file = root / "proposals.json"
            file.write_text(json.dumps(data), encoding="utf-8")
            self.assertIsNone(load_proposal(16,root=root,proposal_path=file))
            data["lessons"]["16"]["phases"][0]["minutes"] = 20
            file.write_text(json.dumps(data), encoding="utf-8")
            self.assertIsNone(load_proposal(16, proposal_path=file))
            data["lessons"]["16"]["phases"][0]["minutes"] = 8
            data["lessons"]["16"]["source_marker"] = "not actually in lesson"
            file.write_text(json.dumps(data), encoding="utf-8")
            self.assertIsNone(load_proposal(16, proposal_path=file))
            data["version"] = "unapproved"
            file.write_text(json.dumps(data), encoding="utf-8")
            self.assertIsNone(load_proposal(16, proposal_path=file))

    def test_idempotent_install_preserves_credits_and_telegram_callback(self):
        calls=[]
        def old_rows(state, ai):
            calls.append((state["lesson_no"],ai))
            return dict(OLD)
        runtime = types.SimpleNamespace(_rph_rows=old_rows,
                    _credit_gate=lambda *a:"credit unchanged",
                    callback=lambda *a:"callback unchanged")
        self.assertTrue(install(runtime))
        self.assertTrue(install(runtime))
        out = runtime._rph_rows({"subject":"English","year":"Year 5",
                                 "lesson_no":88}, "old")
        self.assertIn("My Dream School Day",out["TAJUK"])
        self.assertEqual(calls,[(88,"old")])
        self.assertEqual(runtime._credit_gate(1),"credit unchanged")
        self.assertEqual(runtime.callback("menu"),"callback unchanged")

    def test_native_word_pdf_both_read_shared_rows(self):
        app = (ROOT / "app.py").read_text(encoding="utf-8")
        i = app.rfind("def _create_rph_word(")
        self.assertGreater(i,0)
        self.assertIn("rph = _rph_rows(s, ai_text)",app[i:i+300])
        for field in ("MAIN CONTENT STANDARD","MAIN LEARNING STANDARD",
                      "COMPLEMENTARY CONTENT STANDARD",
                      "COMPLEMENTARY LEARNING STANDARD"):
            self.assertIn(field,app[i:i+2500])
        self.assertIn("_rph_rows(s, ai_text)",app)
        wsgi=(ROOT / "tools/run_telegram_with_curriculum_api.py").read_text(
              encoding="utf-8")
        self.assertIn("install_english_y5_choices(telegram_runtime)",wsgi)


if __name__=="__main__":
    unittest.main()
