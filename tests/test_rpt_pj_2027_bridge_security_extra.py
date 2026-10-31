"""Additional fail-closed regression checks for the RPT 2027 native bridge."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from rpt_pj_2027_app_bridge import route
from rpt_pj_2027_delivery import FILE_PATTERN


class RPTBridgeSecurityRegression(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.send = Mock()
        self.send_document = Mock()

    def invoke(self, cid, data, allowed):
        return route(cid, data, self.root, send=self.send,
                     send_document=self.send_document, allowed=allowed)

    def test_negative_group_id_never_checks_entitlement(self):
        access = Mock(return_value=True)
        self.assertTrue(self.invoke(-100999, "rpt2027_pj_doc:Johor:4", access))
        access.assert_not_called()
        self.send_document.assert_not_called()

    def test_boolean_chat_id_is_rejected(self):
        access = Mock(return_value=True)
        self.assertTrue(self.invoke(True, "rpt2027_pj_doc:Johor:4", access))
        access.assert_not_called()

    def test_resolver_exception_denies_even_with_file_present(self):
        folder = self.root / "RPT_PJ_2027_DOCX"
        folder.mkdir()
        (folder / FILE_PATTERN.format(state="Johor", year=4)).write_bytes(b"fixture")
        def failing(_):
            raise RuntimeError("access service unavailable")
        self.assertTrue(self.invoke(101, "rpt2027_pj_doc:Johor:4", failing))
        self.send_document.assert_not_called()

    def test_callback_path_traversal_is_rejected(self):
        self.assertTrue(self.invoke(101, "rpt2027_pj_doc:../Johor:4", lambda _: True))
        self.send_document.assert_not_called()

    def test_unrelated_callback_not_intercepted(self):
        self.assertFalse(self.invoke(101, "rph_today", lambda _: True))
        self.send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
