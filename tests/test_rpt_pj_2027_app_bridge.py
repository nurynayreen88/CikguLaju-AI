import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from rpt_pj_2027_app_bridge import route
from rpt_pj_2027_delivery import FILE_PATTERN


class TestNativeAppBridge(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.send = Mock()
        self.send_document = Mock()

    def call(self, data, allowed=lambda cid: True):
        return route(111, data, self.root, send=self.send,
                     send_document=self.send_document, allowed=allowed)

    def test_unrelated_callback_untouched(self):
        self.assertFalse(self.call("home"))
        self.send.assert_not_called()

    def test_free_user_cannot_download(self):
        self.assertTrue(self.call("rpt2027_pj_doc:Johor:4", allowed=lambda cid: False))
        self.send_document.assert_not_called()

    def test_missing_assets_preserves_existing_year_placeholder(self):
        self.assertFalse(self.call("rpt2027_year_4"))

    def test_invalid_document_callback_does_not_send(self):
        self.assertTrue(self.call("rpt2027_pj_doc:Johor:99"))
        self.send_document.assert_not_called()

    def test_verified_asset_can_be_sent(self):
        folder = self.root / "RPT_PJ_2027_DOCX"
        folder.mkdir()
        path = folder / FILE_PATTERN.format(state="Johor", year=4)
        path.write_bytes(b"test fixture")
        self.assertTrue(self.call("rpt2027_year_4"))
        self.assertTrue(self.call("rpt2027_pj_year_4"))
        self.assertTrue(self.call("rpt2027_pj_doc:Johor:4"))
        self.send_document.assert_called_once_with(
            111, str(path), "RPT Pendidikan Jasmani 2027")


if __name__ == "__main__":
    unittest.main()
