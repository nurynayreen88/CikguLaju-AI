"""Isolated tests for the Maths Year 4 read-only package gate."""
import importlib.util
import io
import unittest
import zipfile
from pathlib import Path
from tempfile import TemporaryDirectory

from docx import Document
from docx.shared import Mm

SCRIPT = Path(__file__).resolve().parents[1] / "tools" / "check_matematik_t4_package.py"
spec = importlib.util.spec_from_file_location("check_matematik_t4_package", SCRIPT)
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def fake_docx(*, complete=True, a4=True):
    doc = Document()
    if a4:
        doc.sections[0].page_width = Mm(210)
        doc.sections[0].page_height = Mm(297)
    doc.add_paragraph("RPH Matematik Tahun 4 — PRA-READY")
    doc.add_paragraph("RPT 2026 / 2027 belum disahkan; Buku Aktiviti belum disahkan")
    doc.add_paragraph("Set induksi, aktiviti, pentaksiran, penutup dan BBM" if complete else "Set induksi")
    out = io.BytesIO()
    doc.save(out)
    return out.getvalue()


class PackageSafetyTest(unittest.TestCase):
    def make_zip(self, where, *, omit=None, duplicate=False, complete=True):
        path = Path(where) / "package.zip"
        with zipfile.ZipFile(path, "w") as out:
            for lesson_id in sorted(module.EXPECTED_IDS):
                if lesson_id == omit:
                    continue
                out.writestr(f"p/83_RPH_Word/RPH_T4_{lesson_id}_PRA_READY.docx", fake_docx(complete=complete))
            if duplicate:
                out.writestr("q/RPH_T4_01_PRA_READY.docx", fake_docx())
        return path

    def test_83_valid_documents_still_blocked_while_preready(self):
        with TemporaryDirectory() as tmp:
            r = module.audit_zip(self.make_zip(tmp))
            self.assertEqual(r["counts"]["documents"], 83)
            self.assertEqual(r["counts"]["a4"], 83)
            self.assertFalse(r["release_allowed"])
            self.assertFalse(r["production_mutations"])
            self.assertEqual(r["counts"]["preready_marked"], 83)

    def test_missing_id_blocks_release(self):
        with TemporaryDirectory() as tmp:
            r = module.audit_zip(self.make_zip(tmp, omit="11C"))
            self.assertFalse(r["release_allowed"])
            self.assertTrue(any("Missing RPH IDs: 11C" in s for s in r["findings"]))

    def test_duplicate_id_blocks_release(self):
        with TemporaryDirectory() as tmp:
            r = module.audit_zip(self.make_zip(tmp, duplicate=True))
            self.assertTrue(any("Duplicate RPH ID 01" in s for s in r["findings"]))

    def test_incomplete_sections_blocks_release(self):
        with TemporaryDirectory() as tmp:
            r = module.audit_zip(self.make_zip(tmp, complete=False))
            self.assertEqual(r["counts"]["required_sections"], 0)
            self.assertFalse(r["release_allowed"])


if __name__ == "__main__":
    unittest.main()