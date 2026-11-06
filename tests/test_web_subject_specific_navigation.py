"""Web navigation is source-specific, with a numbered Lesson/PdP final choice."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from web.authoritative_http_source import AuthoritativeHttpCurriculumSource
from web.unified_rph_web import _english_page_reference

ROOT = Path(__file__).resolve().parents[1]


class SubjectNavigationQA(unittest.TestCase):
    def test_bm_http_adapter_preserves_exact_unmodified_selection(self):
        source = AuthoritativeHttpCurriculumSource(
            "https://telegram.example", "x" * 40)
        with patch.object(source, "_read", return_value=[]) as reader:
            self.assertEqual(source.list_bm_themes(2), [])
            self.assertEqual(reader.call_args.args[0], "bm-themes")
            self.assertEqual(reader.call_args.args[1]["subject"], "BM")
            source.list_bm_units(2, "Tema 1")
            self.assertEqual(reader.call_args.args,
                             ("bm-units", {"year": 2, "subject": "BM",
                                           "theme": "Tema 1"}))
            source.list_bm_topics(2, "Tema 1", "Keluargaku")
            self.assertEqual(reader.call_args.args,
                             ("bm-topics", {"year": 2, "subject": "BM",
                                            "theme": "Tema 1", "unit": "Keluargaku"}))
            source.list_bm_pdps(2, "Tema 1", "Keluargaku", "Ceria Pagi")
            self.assertEqual(reader.call_args.args,
                             ("bm-pdp", {"year": 2, "subject": "BM",
                                         "theme": "Tema 1", "unit": "Keluargaku",
                                         "topic": "Ceria Pagi"}))
            for bad in ("", " "*5, "x"*301, "\nmalformed"):
                with self.subTest(bad=repr(bad)), self.assertRaises(ValueError):
                    source.list_bm_units(2, bad)

    def test_navigation_order_and_subject_specific_final_step(self):
        html = (ROOT / "web_v1_static_preview/index.html").read_text(encoding="utf-8")
        self.assertLess(html.index('id="subject"'), html.index('id="theme"'))
        self.assertLess(html.index('id="theme"'), html.index('id="unit"'))
        self.assertLess(html.index('id="unit"'), html.index('id="topic"'))
        self.assertLess(html.index('id="topic"'), html.index('id="lesson"'))
        for term in ("bm-themes", "bm-units", "bm-topics", "bm-pdp",
                     "setSubjectNavigationLabels", "subjectNavLabel",
                     "sourceUnitLabel", "numberedPdpLabel",
                     "displayBookReference", "lesson-source-pages"):
            self.assertIn(term, html)
        self.assertIn('code==="BM"', html)
        self.assertIn('code==="ENGLISH"?"Lesson":"PdP"', html)
        self.assertIn('item.textbook_ref||item.student_book_ref', html)

    def test_english_page_refs_are_stated_in_source_not_guessed(self):
        existing = ROOT / "rph_standalone/english/year3/lesson_013.md"
        self.assertEqual(_english_page_reference(existing),
                         "Student's Book m/s 11")
        with tempfile.TemporaryDirectory() as folder:
            p = Path(folder) / "test.md"
            p.write_text("RPH Lesson 20. No confirmed Student's Book pages",
                         encoding="utf-8")
            self.assertEqual(_english_page_reference(p), "")
            p.write_text("**Materials:** SB p.19; Teacher's Book p.23",
                         encoding="utf-8")
            self.assertEqual(_english_page_reference(p), "Student's Book m/s 19")


if __name__ == "__main__":
    unittest.main()
