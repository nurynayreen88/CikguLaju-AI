"""Ensure RPT document delivery does not follow an untrusted asset root."""
import tempfile
import unittest
from pathlib import Path

from rpt_pj_2027_delivery import (
    RPTDocumentUnavailable, list_available, resolve_rpt,
)


class DeliveryRootSafetyTests(unittest.TestCase):
    def test_symlinked_root_is_not_listed_or_served(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            actual = base / "real"
            actual.mkdir()
            (actual / "RPT_PJ_2027_DOCX").mkdir()
            linked = base / "linked"
            try:
                linked.symlink_to(actual, target_is_directory=True)
            except (OSError, NotImplementedError):
                self.skipTest("Directory symlinks unavailable")
            self.assertEqual(list_available(linked), [])
            with self.assertRaises(RPTDocumentUnavailable):
                resolve_rpt(linked, negeri="Kedah", tahun=4, authorized=True)

    def test_unauthorized_request_is_rejected_first(self):
        with tempfile.TemporaryDirectory() as folder:
            from rpt_pj_2027_delivery import RPTAccessDenied
            with self.assertRaises(RPTAccessDenied):
                resolve_rpt(folder, negeri="Kedah", tahun=4, authorized=False)


if __name__ == "__main__":
    unittest.main()
