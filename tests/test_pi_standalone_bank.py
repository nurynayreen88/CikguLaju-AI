import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.validate_pi_standalone_bank import validate


class StandaloneBankTest(unittest.TestCase):
    def test_approved_requires_real_unchanged_pdf(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pdf").mkdir()
            import fitz
            doc = fitz.open()
            doc.new_page(width=595.28, height=841.89).insert_text((50, 50), "RPH Pendidikan Islam")
            payload = doc.tobytes()
            doc.close()
            (root / "pdf/PI-Y1-L001.pdf").write_bytes(payload)
            item = dict(year=1, lesson_id="PI-Y1-L001", sk="1.1", sp="1.1.1",
                        pdf="pdf/PI-Y1-L001.pdf", status="approved",
                        sha256=hashlib.sha256(payload).hexdigest())
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(dict(schema_version=1, items=[item])))
            self.assertEqual(validate(manifest)["errors"], [])
            (root / "pdf/PI-Y1-L001.pdf").write_bytes(payload+b"tampered")
            self.assertTrue(any("checksum mismatch" in x for x in validate(manifest)["errors"]))

    def test_unapproved_is_not_counted(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            item = dict(year=2, lesson_id="PI-Y2-L001", sk="1.1", sp="1.1.1",
                        pdf="pdf/PI-Y2-L001.pdf", status="review")
            manifest.write_text(json.dumps(dict(schema_version=1, items=[item])))
            self.assertEqual(validate(manifest)["approved"], 0)

    def test_path_escape_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            manifest = Path(tmp) / "manifest.json"
            item = dict(year=1, lesson_id="PI-Y1-L001", sk="1", sp="1",
                        pdf="../outside.pdf", status="approved", sha256="0"*64)
            manifest.write_text(json.dumps(dict(schema_version=1, items=[item])))
            self.assertTrue(any("escapes" in x for x in validate(manifest)["errors"]))


    def test_approved_rejects_two_page_pdf(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pdf").mkdir()
            doc = fitz.open()
            doc.new_page(width=595.28, height=841.89)
            doc.new_page(width=595.28, height=841.89).insert_text((50, 50), "RPH Pendidikan Islam")
            payload = doc.tobytes()
            doc.close()
            (root / "pdf/PI-Y1-L002.pdf").write_bytes(payload)
            item = dict(year=1, lesson_id="PI-Y1-L002", sk="1.1", sp="1.1.1",
                        pdf="pdf/PI-Y1-L002.pdf", status="approved",
                        sha256=hashlib.sha256(payload).hexdigest())
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(dict(schema_version=1, items=[item])))
            self.assertTrue(any("one A4 page" in x for x in validate(manifest)["errors"]))

    def test_approved_rejects_blank_pdf(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pdf").mkdir()
            doc = fitz.open()
            doc.new_page(width=595.28, height=841.89)
            payload = doc.tobytes()
            doc.close()
            (root / "pdf/PI-Y1-L004.pdf").write_bytes(payload)
            item = dict(year=1, lesson_id="PI-Y1-L004", sk="1.1", sp="1.1.1",
                        pdf="pdf/PI-Y1-L004.pdf", status="approved",
                        sha256=hashlib.sha256(payload).hexdigest())
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(dict(schema_version=1, items=[item])))
            self.assertTrue(any("blank" in x for x in validate(manifest)["errors"]))

    def test_approved_rejects_landscape_pdf(self):
        import fitz
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "pdf").mkdir()
            doc = fitz.open()
            doc.new_page(width=841.89, height=595.28)
            payload = doc.tobytes()
            doc.close()
            (root / "pdf/PI-Y1-L003.pdf").write_bytes(payload)
            item = dict(year=1, lesson_id="PI-Y1-L003", sk="1.1", sp="1.1.1",
                        pdf="pdf/PI-Y1-L003.pdf", status="approved",
                        sha256=hashlib.sha256(payload).hexdigest())
            manifest = root / "manifest.json"
            manifest.write_text(json.dumps(dict(schema_version=1, items=[item])))
            self.assertTrue(any("A4 portrait" in x for x in validate(manifest)["errors"]))


if __name__ == "__main__":
    unittest.main()
