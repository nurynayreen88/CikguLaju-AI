"""Double-opt-in startup migration: no service import, no network side effects."""
import ast
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
MODULE = ROOT / "tools" / "run_web_production.py"
FLAG = "CIKGULAJU_PRIVATE_WORD_MIGRATION_ON_START"
ALLOW = "CIKGULAJU_PRIVATE_WORD_MIGRATION_OK"


def _function():
    root = ast.parse(MODULE.read_text("utf-8"), filename=str(MODULE))
    funcs = [node for node in root.body
             if isinstance(node, ast.FunctionDef)
             and node.name == "_private_bm_word_startup_migration"]
    if len(funcs) != 1:
        raise AssertionError("Expected one guarded migration entry point")
    namespace = {"os": os}
    exec(compile(ast.Module(body=funcs, type_ignores=[]), str(MODULE), "exec"),
         namespace)
    return namespace[funcs[0].name]


class TestServerOnlyStartupMigration(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.invoke_migration = staticmethod(_function())

    def test_no_environment_flag_is_noop(self):
        with patch.dict(os.environ, {FLAG: "", ALLOW: "YES"}):
            self.assertEqual(self.invoke_migration(), "DISABLED")

    def test_second_approval_missing_never_runs(self):
        with patch.dict(os.environ, {FLAG: "RPT_BM_2027_V1", ALLOW: ""}):
            self.assertEqual(self.invoke_migration(), "DISABLED")

    def test_both_optins_verify_exact_five_or_fail_closed(self):
        with patch.dict(os.environ, {FLAG: "RPT_BM_2027_V1", ALLOW: "YES"}), \
             patch("tools.migrate_rpt_bm_kssr_word_private.migrate",
                   return_value=[2, 3, 4, 5, 6]) as migrate:
            self.assertEqual(self.invoke_migration(), "VERIFIED")
            migrate.assert_called_once_with(upload=True)

    def test_partial_or_failed_migration_never_marks_verified(self):
        with patch.dict(os.environ, {FLAG: "RPT_BM_2027_V1", ALLOW: "YES"}), \
             patch("tools.migrate_rpt_bm_kssr_word_private.migrate",
                   return_value=[2, 3, 4]):
            self.assertEqual(self.invoke_migration(), "FAILED")

    def test_sensitive_exception_body_never_printed(self):
        output = StringIO()
        with patch.dict(os.environ, {FLAG: "RPT_BM_2027_V1", ALLOW: "YES"}), \
             patch("tools.migrate_rpt_bm_kssr_word_private.migrate",
                   side_effect=ValueError("secret-token-DO-NOT-PRINT")), \
             redirect_stdout(output):
            self.assertEqual(self.invoke_migration(), "FAILED")
        self.assertNotIn("secret-token", output.getvalue())
