"""Static integration regression checks for the final app.py wrappers.

These checks do not import app.py or touch production databases.
"""
import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
TREE = ast.parse((ROOT / 'app.py').read_text(encoding='utf-8'))


class AdminUsageIntegrationTests(unittest.TestCase):
    def test_last_flask_app_is_followed_by_usage_webhook_wrap(self):
        app_assignments = [
            node.lineno for node in TREE.body
            if isinstance(node, ast.Assign)
            and any(isinstance(t, ast.Name) and t.id == 'app' for t in node.targets)
        ]
        wrappers = [
            node for node in TREE.body if isinstance(node, ast.If)
            and any(isinstance(n, ast.FunctionDef) and n.name == '_admin_usage_webhook'
                    for n in ast.walk(node))
        ]
        self.assertTrue(app_assignments, 'No Flask app assignment')
        self.assertEqual(len(wrappers), 1, 'Missing or duplicate usage webhook wrapper')
        self.assertGreater(wrappers[0].lineno, max(app_assignments))
        source = ast.get_source_segment((ROOT / 'app.py').read_text(encoding='utf-8'), wrappers[0])
        self.assertIn("app.view_functions['webhook'] = _admin_usage_webhook", source)
        self.assertIn("return _ADMIN_USAGE_WEBHOOK_BASE()", source)
        self.assertIn('record_daily_active(connection, user_id)', source)

    def test_callback_and_delivery_wrapper_exist(self):
        callbacks = [n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'callback']
        self.assertTrue(callbacks)
        # Later compatibility wrappers delegate to the earlier admin callback.
        self.assertTrue(any("d == 'admin_usage_stats'" in ast.unparse(n) and
                            'show_admin_usage(cid, _is_admin, _db, send)' in ast.unparse(n)
                            for n in callbacks))
        sends = [n for n in TREE.body if isinstance(n, ast.FunctionDef) and n.name == 'send_document']
        self.assertGreaterEqual(len(sends), 2)
        last = ast.unparse(sends[-1])
        self.assertIn('_ADMIN_USAGE_SEND_DOCUMENT_BASE(cid, path, caption)', last)
        self.assertIn('record_confirmed_delivery(', last)
        self.assertIn('return result', last)


if __name__ == '__main__':
    unittest.main()
