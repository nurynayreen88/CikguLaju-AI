"""Ensure direct RPT asset installation cannot overwrite existing data."""
import tempfile
import unittest
from pathlib import Path

from scripts.install_rpt_pj_2027_assets import install


class RPTInstallDestinationTests(unittest.TestCase):
    def test_existing_folder_rejected_before_archive_read(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            existing = root / "release"
            existing.mkdir()
            marker = existing / "keep.txt"
            marker.write_text("preserve")
            with self.assertRaises(FileExistsError):
                install(root / "missing.zip", existing)
            self.assertEqual(marker.read_text(), "preserve")

    def test_existing_file_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "file"
            target.write_text("preserve")
            with self.assertRaises(FileExistsError):
                install(root / "missing.zip", target)
            self.assertEqual(target.read_text(), "preserve")


if __name__ == "__main__":
    unittest.main()
