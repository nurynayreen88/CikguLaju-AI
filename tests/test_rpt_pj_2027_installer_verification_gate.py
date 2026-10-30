"""The direct installer must fail closed before creating a destination."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.install_rpt_pj_2027_assets import install


class InstallerVerificationGateTests(unittest.TestCase):
    def test_invalid_archive_cannot_create_destination(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            archive = root / "bad.zip"
            archive.write_bytes(b"not a zip archive")
            destination = root / "new-assets"
            with self.assertRaises(ValueError):
                install(archive, destination)
            self.assertFalse(destination.exists())

    def test_content_validation_failure_prevents_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / "new-assets"
            with patch("scripts.install_rpt_pj_2027_assets.verify",
                       return_value=["Missing PdP sequence"]):
                with self.assertRaisesRegex(ValueError, "verification failed"):
                    install(root / "not-needed.zip", destination)
            self.assertFalse(destination.exists())


if __name__ == "__main__":
    unittest.main()
