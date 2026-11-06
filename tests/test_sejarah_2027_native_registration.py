"""Verify private Sejarah Web bridge is registered without booting Telegram."""
import ast
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]


class SejarahRegistrationTest(unittest.TestCase):
    def test_registration_comes_after_native_user_bridge(self):
        source=(ROOT/"tools/run_telegram_with_curriculum_api.py").read_text(encoding="utf-8")
        tree=ast.parse(source)
        first=source.index("SEJARAH_2027_USER_BRIDGE_ACTIVE = bool(")
        second=source.index("create_sejarah_2027_native_blueprint(telegram_runtime)")
        self.assertLess(first,second)
        self.assertEqual(source.count("create_sejarah_2027_native_blueprint(telegram_runtime)"),1)
        self.assertIn("SEJARAH_2027_WEB_READER_REGISTERED = False",source)
        self.assertNotIn("CIKGULAJU_SEJARAH_2027_USER_ENABLED=1",source)
        self.assertNotIn("teacher_approval=True",source)
        self.assertIsNotNone(tree)

    def test_no_unapproved_source_is_mislabelled_final(self):
        from web.sejarah_2027_user_runtime import _catalog
        for year in (4,5,6):
            rows=_catalog(year,str(ROOT))
            self.assertEqual(len(rows),36)
            for item in rows:
                rph=item["rph"]
                self.assertFalse(rph["teacher_approval"])
                self.assertFalse(rph["textbook_page_verified"])
                self.assertTrue(rph["status"].startswith("DRAF"))


if __name__=="__main__":
    unittest.main()
