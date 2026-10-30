"""Corrupt archive must fail validation without crashing release tooling."""
import tempfile
import unittest
from pathlib import Path

from scripts.verify_rpt_pj_2027_v76 import verify


class RPTArchiveCorruptionTests(unittest.TestCase):
    def test_invalid_zip_returns_failure_list(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "invalid.zip"
            archive.write_bytes(b"not a zip file")
            errors = verify(archive)
            self.assertTrue(errors)
            self.assertIn("Invalid RPT archive", errors[0])

    def test_missing_zip_returns_failure_list(self):
        with tempfile.TemporaryDirectory() as folder:
            errors = verify(Path(folder) / "missing.zip")
            self.assertTrue(errors)


if __name__ == "__main__":
    unittest.main()
