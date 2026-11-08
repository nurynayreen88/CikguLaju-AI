"""Unit tests for internal developer-note leakage into RPT teacher documents."""
import tempfile
import unittest
from pathlib import Path

from scripts.audit_rpt2027_teacher_text_leaks_20261108 import (
    find_internal_notes, scan_paths,
)


class TeacherTextLeakAuditTests(unittest.TestCase):
    def test_original_pendidikan_islam_leak_is_detected(self):
        text = "Pemetaan buku teks belum disahkan; rujuk buku dan DSKP sebelum READY."
        rules = {item["rule"] for item in find_internal_notes(text)}
        self.assertIn("TEXTBOOK_MAPPING_REVIEW", rules)
        self.assertIn("DEVELOPER_INSTRUCTION", rules)
        self.assertIn("READY_INTERNAL", rules)

    def test_math_bm_psv_and_rbt_editor_messages_are_detected(self):
        examples = (
            "DRAF TERKAWAL / PRA-READY",
            "Pengesahan instrumen belum selesai.",
            "Buku Aktiviti belum disahkan.",
            "Semak tajuk penuh",
            "4, 7 (calon teks digital; belum sah)",
            "STATUS DRAF — halaman latihan dan cuti negeri belum lengkap",
            "Tiada janaan automatik sehingga pengesahan selesai.",
        )
        for sample in examples:
            with self.subTest(sample=sample):
                self.assertTrue(find_internal_notes(sample))

    def test_legitimate_pedagogical_language_does_not_trigger(self):
        clean = (
            "Murid membaca petikan dan menjawab tiga soalan. "
            "Guru membuat semakan bahan bertulis, merekod PBD dan "
            "menjalankan aktiviti berdasarkan Standard Pembelajaran 2.3.1. "
            "Buku Teks halaman 21."
        )
        self.assertEqual(find_internal_notes(clean), [])

    def test_unreadable_pdf_and_empty_folder_fail_closed(self):
        import contextlib
        import io
        from scripts.audit_rpt2027_teacher_text_leaks_20261108 import main
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            corrupt = folder / "rpt_corrupt.pdf"
            corrupt.write_bytes(b"%PDF-corrupt-not-real")
            # This is an error, not a clean document with zero findings.
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(corrupt)]), 1)
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(main([str(folder / "missing")]), 1)

    def test_scan_teacher_output_separately_from_source_data(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "rpt.html").write_text(
                "<html><p>Semak tajuk penuh</p></html>", encoding="utf-8"
            )
            (root / "source.csv").write_text(
                "nota\nPemetaan buku teks belum disahkan\n", encoding="utf-8"
            )
            teacher = scan_paths([root], teacher_output_only=True)
            self.assertEqual(teacher["scanned_files"], 1)
            self.assertEqual(teacher["files_with_findings"], 1)
            self.assertFalse(teacher["read_errors"])
            full = scan_paths([root])
            self.assertEqual(full["scanned_files"], 2)
            self.assertEqual(full["files_with_findings"], 2)
            self.assertFalse(full["academic_signoff"])


if __name__ == "__main__":
    unittest.main()
