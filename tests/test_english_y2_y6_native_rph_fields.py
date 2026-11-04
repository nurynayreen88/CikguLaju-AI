"""Cross-year native Word/PDF source tests — English Year 2–6 only.

No production app import, database writes or quota transactions. Tests the
actual row contracts used by both English Word and PDF document generators.
"""
import json
import os
from pathlib import Path
import types
import unittest
from unittest.mock import patch

from english_y2_standalone_render import apply as year2_activities
from english_y3_standalone_render import apply as year3_activities
from web.english_y2_y3_standard_runtime import (
    SOW_INDEX, enrich_rows, install as install_y2_y3, _year_and_lesson,
)
from web.english_y4_standalone_runtime import adapt_rows as year4_rows
from web.english_y5_standalone_runtime import (
    CHOICE_LESSONS as Y5_TEACHER_CHOICES,
    RELEASE_FLAG as Y5_RELEASE_FLAG,
    adapt_rows as year5_staged,
    install as install_y5,
)
from web.english_y6_standalone_runtime import adapt_rows as year6_rows

REPO = Path(__file__).resolve().parents[1]
DATA = json.loads(SOW_INDEX.read_text(encoding="utf-8"))
BASE = {
    "MATA PELAJARAN": "English", "TARIKH": "04/11/2026",
    "KELAS": "5 Cekap", "MASA": "08:00",
    "BILANGAN MURID": "31", "REFLEKSI": "Teacher entered",
    "MAIN LEARNING STANDARD": "LEGACY MAIN",
    "COMPLEMENTARY LEARNING STANDARD": "LEGACY COMP",
    "OBJEKTIF PEMBELAJARAN": "Old generic objectives",
}


class CrossYearEnglishDocumentRows(unittest.TestCase):
    def test_year2_year3_paired_sow_document_coverage(self):
        counts = {}
        for year, renderer in ((2, year2_activities), (3, year3_activities)):
            valid, rejected, old_objectives = [], [], []
            for number in range(1, 161):
                source = DATA["lessons"][f"{year}/{number}"]
                st = {"year": f"Tahun {year}", "subject": "English",
                      "lesson_no": number,
                      "sp_code": source["main_ls"],
                      "comp_sp_code": source["complementary_ls"]}
                underlying = renderer(st, dict(BASE))
                result = enrich_rows(st, underlying)
                if result.get("MAIN LEARNING STANDARD") == source["main_ls"]:
                    valid.append(number)
                    self.assertEqual(result["COMPLEMENTARY LEARNING STANDARD"],
                                     source["complementary_ls"])
                    self.assertEqual(result["MAIN CONTENT STANDARD"],
                                     source["main_ls"].rsplit(".", 1)[0])
                    self.assertEqual(result["COMPLEMENTARY CONTENT STANDARD"],
                                     source["complementary_ls"].rsplit(".", 1)[0])
                    self.assertEqual(result["TARIKH"], BASE["TARIKH"])
                    self.assertEqual(result["REFLEKSI"], BASE["REFLEKSI"])
                    if result.get("OBJEKTIF PEMBELAJARAN") == BASE["OBJEKTIF PEMBELAJARAN"]:
                        old_objectives.append(number)
                else:
                    rejected.append(number)
            counts[year] = (len(valid), rejected)
            print(f"YEAR{year} SOW_METADATA_MATCHED={len(valid)}/160 REJECTED={rejected} "
                  f"OBJECTIVE_SOURCE_MISSING={old_objectives}",
                  flush=True)
            # Any rejected lesson is still served by the preexisting generator;
            # we do not fabricate a code to force it to pass.
            self.assertGreaterEqual(len(valid), 140, "Unexpectedly low validated source coverage")
        self.assertEqual(len(counts), 2)

    def test_y2_y3_invalid_selection_and_mismatched_sow_do_not_update(self):
        valid = {"year": "Tahun 3", "subject": "English",
                 "lesson_no": 93, "sp_code": "3.2.1",
                 "comp_sp_code": "4.2.5"}
        source_rows = year3_activities(valid, dict(BASE))
        self.assertIn("_standalone_y3_source", source_rows)
        for change in ({"sp_code": "1.2.2"}, {"comp_sp_code": "1.2.2"},
                       {"lesson_no": "not-number"}, {"year": "Tahun 5"},
                       {"subject": "Matematik"}):
            with self.subTest(change=change):
                self.assertIs(enrich_rows({**valid, **change}, source_rows), source_rows)
        rows = dict(BASE)
        self.assertIs(enrich_rows(valid, rows), rows)
        self.assertIsNone(_year_and_lesson({"year": "Year 3",
                                            "subject": "English", "lesson_no": True}))
        self.assertIsNone(_year_and_lesson({"year": "Year 1",
                                            "subject": "English", "lesson_no": 1}))

    def test_y2_y3_bridge_runs_after_previous_renderer_only_once(self):
        state = {"year": "Tahun 3", "subject": "English", "lesson_no": 93,
                 "sp_code": "3.2.1", "comp_sp_code": "4.2.5"}
        calls = []
        def previous(st, ai):
            calls.append(ai)
            return year3_activities(st, dict(BASE))
        runtime = types.SimpleNamespace(_rph_rows=previous,
                                        debit=lambda *_: "unchanged")
        self.assertTrue(install_y2_y3(runtime))
        self.assertTrue(install_y2_y3(runtime))
        doc = runtime._rph_rows(state, "sample")
        self.assertEqual(doc["MAIN LEARNING STANDARD"], "3.2.1")
        self.assertEqual(doc["COMPLEMENTARY LEARNING STANDARD"], "4.2.5")
        self.assertEqual(doc["TARIKH"], BASE["TARIKH"])
        self.assertEqual(runtime.debit(42), "unchanged")
        self.assertEqual(calls, ["sample"])

    def test_year4_remains_isolated(self):
        st = {"year": "Year 4", "subject": "English", "lesson_no": 1,
              "sp_code": "1.2.2", "comp_sp_code": "1.1.1"}
        out = year4_rows(st, dict(BASE))
        self.assertEqual(out["MAIN LEARNING STANDARD"], "1.2.2")
        self.assertEqual(out["COMPLEMENTARY LEARNING STANDARD"], "1.1.1")
        self.assertEqual(out["TARIKH"], BASE["TARIKH"])

    def test_year6_word_pdf_main_complementary_fields_not_legacy(self):
        for number in (1, 15, 21, 25, 26, 37, 160):
            with self.subTest(lesson=number):
                record = DATA["lessons"][f"6/{number}"]
                st = {"year": "Tahun 6", "subject": "English", "lesson_no": number}
                if not record["teacher_selected"]:
                    st["sp_code"] = record["main_ls"]
                    st["comp_sp_code"] = record["complementary_ls"]
                out = year6_rows(st, dict(BASE))
                if record["teacher_selected"]:
                    # Do not manufacture official fixed SOW standards.
                    self.assertNotEqual(out.get("MAIN LEARNING STANDARD"),
                                        record["main_ls"])
                    continue
                self.assertEqual(out["MAIN LEARNING STANDARD"], record["main_ls"])
                self.assertEqual(out["COMPLEMENTARY LEARNING STANDARD"],
                                 record["complementary_ls"])
                self.assertNotIn("LEGACY", out["MAIN LEARNING STANDARD"])
                self.assertEqual(out["TARIKH"], BASE["TARIKH"])
                self.assertIn("Teacher:", out["AKTIVITI UTAMA"])
                self.assertIn("Pupils:", out["AKTIVITI UTAMA"])

    def test_year6_mismatched_comp_sow_keeps_existing_fields(self):
        state = {"year": "Year 6", "subject": "English", "lesson_no": 1,
                 "sp_code": "3.2.1", "comp_sp_code": "1.2.2"}
        self.assertIs(year6_rows(state, BASE), BASE)

    def test_year5_staged_151_but_draft_download_remains_disabled(self):
        with patch.dict(os.environ, {}, clear=True):
            runtime = types.SimpleNamespace(_rph_rows=lambda *_: dict(BASE))
            self.assertFalse(install_y5(runtime))
        fixed, mismatches = [], []
        for number in range(1, 161):
            rec = DATA["lessons"][f"5/{number}"]
            st = {"year": "Tahun 5", "subject": "English", "lesson_no": number}
            out = year5_staged(st, dict(BASE))
            if rec["teacher_selected"]:
                self.assertIn(number, Y5_TEACHER_CHOICES)
                continue
            fixed.append(number)
            if out.get("STANDARD PEMBELAJARAN", "").find(str(rec["main_ls"])) < 0:
                mismatches.append(number)
        print("YEAR5_STAGING_FIXED", len(fixed),
              "SOURCE_MISMATCHES", mismatches,
              "PRODUCTION_DRAFT_FLAG", Y5_RELEASE_FLAG, flush=True)
        self.assertEqual(len(fixed), 151)
        self.assertFalse(mismatches)

    def test_native_english_document_table_and_wsgi_integration(self):
        # Static source binding of actual Word/PDF generator. No bot import.
        source = (REPO / "app.py").read_text(encoding="utf-8")
        idx = source.rfind("def _create_rph_word(")
        self.assertGreater(idx, 0)
        rendered = source[idx:idx + 4200]
        for field in ("MAIN CONTENT STANDARD", "MAIN LEARNING STANDARD",
                      "COMPLEMENTARY CONTENT STANDARD", "COMPLEMENTARY LEARNING STANDARD"):
            self.assertIn(field, rendered)
        self.assertIn("rph = _rph_rows(s, ai_text)", rendered)
        self.assertIn("def create_pdf_file(", source)
        wsgi = (REPO / "tools/run_telegram_with_curriculum_api.py").read_text(
            encoding="utf-8")
        self.assertIn("install_english_y2_y3_sow_fields(telegram_runtime)", wsgi)
        self.assertIn("install_english_y6_rph(telegram_runtime)", wsgi)
        self.assertIn("install_english_y4_rows(telegram_runtime)", wsgi)


if __name__ == "__main__":
    unittest.main()
