import tempfile
import unittest
from pathlib import Path

from scripts.provision_rpt_pj_2027_v76 import provision, EXPECTED_ARCHIVE_SHA256


class TestPinnedProvisioning(unittest.TestCase):
    def test_hash_is_fixed(self):
        self.assertEqual(len(EXPECTED_ARCHIVE_SHA256), 64)
        self.assertTrue(all(c in "0123456789abcdef" for c in EXPECTED_ARCHIVE_SHA256))

    def test_modified_archive_is_rejected_without_creating_data(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "changed.zip"
            archive.write_bytes(b"tampered")
            destination = root / "new_data"
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                provision(archive, destination)
            self.assertFalse(destination.exists())

    def test_existing_data_directory_is_preserved(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "changed.zip"
            archive.write_bytes(b"tampered")
            destination = root / "existing"
            destination.mkdir()
            marker = destination / "important.db"
            marker.write_text("DO NOT MODIFY")
            with self.assertRaises(ValueError):
                provision(archive, destination)
            self.assertEqual(marker.read_text(), "DO NOT MODIFY")


if __name__ == "__main__":
    unittest.main()
