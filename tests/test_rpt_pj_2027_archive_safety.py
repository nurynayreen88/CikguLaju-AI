"""Regression tests for malformed RPT v76 archive entries."""
import tempfile
import unittest
import warnings
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

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

    def test_extreme_compression_ratio_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / 'compressed.zip'
            with ZipFile(archive, 'w', compression=ZIP_DEFLATED) as zf:
                zf.writestr('repeated.txt', 'A' * 500000)
            self.assertIn('compression ratio', verify(archive)[0])

    def test_parent_directory_member_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "traversal.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("../outside.txt", "unsafe")
            self.assertIn("Unsafe archive member path", verify(archive)[0])

    def test_backslash_member_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "backslash.zip"
            with ZipFile(archive, "w") as zf:
                zf.writestr("RPT_PJ_2027_DOCX\\unexpected.docx", "unsafe")
            self.assertIn("Unsafe archive member path", verify(archive)[0])

    def test_invalid_zip_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            archive = Path(folder) / "invalid.zip"
            archive.write_bytes(b"not a zip file")
            self.assertTrue(verify(archive))


if __name__ == "__main__":
    unittest.main()
