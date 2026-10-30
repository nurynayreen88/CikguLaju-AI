"""Read-only and non-destructive v76 provisioning regression tests."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.provision_rpt_pj_2027_v76 import provision


class RPTProvisionSafetyTests(unittest.TestCase):
    def test_missing_archive_does_not_create_destination(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            target = base / "new_release"
            with self.assertRaises(FileNotFoundError):
                provision(base / "missing.zip", target)
            self.assertFalse(target.exists())

    def test_existing_destination_is_not_modified(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "dummy.zip"
            archive.write_bytes(b"not the approved archive")
            target = base / "existing"
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("do not change")
            with self.assertRaises(FileExistsError):
                provision(archive, target)
            self.assertEqual(marker.read_text(), "do not change")

    def test_symlink_destination_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            archive = base / "dummy.zip"
            archive.write_bytes(b"not the approved archive")
            existing = base / "existing"
            existing.mkdir()
            link = base / "link"
            try:
                link.symlink_to(existing, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks not available on this platform")
            with self.assertRaises(FileExistsError):
                provision(archive, link)
            self.assertTrue(link.is_symlink())


if __name__ == "__main__":
    unittest.main()
