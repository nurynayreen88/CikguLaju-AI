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
            payload = b"%PDF-1.4\nexample"
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


if __name__ == "__main__":
    unittest.main()
