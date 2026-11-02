"""Verify Web never claims shared-source parity for a copied catalog."""
import tempfile
import unittest
from pathlib import Path
from web.shared_source_provenance import catalog_source_status


class SharedSourceTests(unittest.TestCase):
    def test_unconfigured_fails_closed(self):
        self.assertFalse(catalog_source_status({})["shared_source_verified"])

    def test_same_local_file_is_not_proof_of_live_sync(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "catalog.sqlite"
            path.write_bytes(b"test")
            result = catalog_source_status({
                "CIKGULAJU_WEB_PREVIEW_DB": str(path),
                "CIKGULAJU_SHARED_CATALOG_DB": str(path)})
            self.assertFalse(result["shared_source_verified"])
            self.assertTrue(result["same_local_file"])

    def test_copy_is_not_shared(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = Path(folder) / "a.db", Path(folder) / "b.db"
            a.write_bytes(b"same bytes")
            b.write_bytes(b"same bytes")
            result = catalog_source_status({
                "CIKGULAJU_WEB_PREVIEW_DB": str(a),
                "CIKGULAJU_SHARED_CATALOG_DB": str(b)})
            self.assertFalse(result["shared_source_verified"])


if __name__ == "__main__":
    unittest.main()
