import tempfile
import unittest
from unittest.mock import patch
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

    def test_postinstall_failure_rolls_back_new_directory(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            archive = root / "approved.zip"
            archive.write_bytes(b"fixture")
            destination = root / "new_data"

            def fake_install(_archive, target):
                target.mkdir()
                (target / "partial.docx").write_bytes(b"partial")
                return 1

            with patch("scripts.provision_rpt_pj_2027_v76.hashlib.sha256") as sha, \\
                 patch("scripts.provision_rpt_pj_2027_v76.verify", return_value=[]), \\
                 patch("scripts.provision_rpt_pj_2027_v76.install", side_effect=fake_install):
                sha.return_value.hexdigest.return_value = EXPECTED_ARCHIVE_SHA256
                with self.assertRaisesRegex(RuntimeError, "incomplete"):
                    provision(archive, destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
