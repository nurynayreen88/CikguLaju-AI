"""Fail-safe behaviour when RPT assets are unavailable or corrupt."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from rpt_pj_2027_app_bridge import route


class RPTCatalogueFailureTests(unittest.TestCase):
    def test_catalogue_read_error_returns_user_message(self):
        with tempfile.TemporaryDirectory() as root:
            send = Mock()
            document = Mock()
            with patch("rpt_pj_2027_app_bridge.list_available", side_effect=OSError("disk")):
                handled = route(123, "rpt2027_pj_year_4", Path(root),
                                send=send, send_document=document,
                                allowed=lambda _: True)
            self.assertTrue(handled)
            send.assert_called_once()
            document.assert_not_called()

    def test_catalogue_read_error_does_not_bypass_entitlement(self):
        with tempfile.TemporaryDirectory() as root:
            send = Mock()
            document = Mock()
            with patch("rpt_pj_2027_app_bridge.list_available") as listing:
                handled = route(123, "rpt2027_pj_year_4", Path(root),
                                send=send, send_document=document,
                                allowed=lambda _: False)
                listing.assert_not_called()
            self.assertTrue(handled)
            document.assert_not_called()


if __name__ == "__main__":
    unittest.main()
