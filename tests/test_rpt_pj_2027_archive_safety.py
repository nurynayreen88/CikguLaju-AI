"""Regression tests for malformed RPT v76 archive entries."""
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZipInfo

from scripts.verify_rpt_pj_2027_v76 import verify


class RPTArchiveSafetyTests(unittest.TestCase):
    def test_duplicate_directory_entries_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "duplicate.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", UserWarning)
                with ZipFile(archive, "w") as zf:
                    zf.writestr("RPT_PJ_2027_DOCX/", "")
                    zf.writestr("RPT_PJ_2027_DOCX/", "")
            self.assertIn("Duplicate archive entries", verify(archive)[0])

    def test_unexpected_member_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "extra.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("extra.txt", "not an approved RPT")
            self.assertTrue(verify(archive))

    def test_invalid_zip_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "invalid.zip"
            archive.write_bytes(b"not a zip file")
            self.assertTrue(verify(archive))


if __name__ == "__main__":
    unittest.main()
