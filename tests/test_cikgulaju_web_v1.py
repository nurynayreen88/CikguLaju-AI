"""Regression tests for the isolated, disabled-by-default web scaffold.

Run: python -m unittest discover -s tests -p 'test_cikgulaju_web_v1.py'
"""
import unittest
from flask import Flask
from cikgulaju_web_v1 import register_web_v1, web_v1


class WebV1SafetyTests(unittest.TestCase):
    def test_web_not_registered_by_default(self):
        app = Flask(__name__)
        self.assertFalse(register_web_v1(app))
        self.assertNotIn("cikgulaju_web_v1", app.blueprints)
        self.assertEqual(app.test_client().get("/web/health").status_code, 404)

    def test_explicit_enable_fails_closed(self):
        app = Flask(__name__)
        with self.assertRaisesRegex(RuntimeError, "cannot be enabled"):
            register_web_v1(app, enabled=True)
        self.assertNotIn("cikgulaju_web_v1", app.blueprints)

    def test_blueprint_health_only_when_manually_registered_in_test(self):
        app = Flask(__name__)
        app.register_blueprint(web_v1)
        response = app.test_client().get("/web/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "scaffold-only")


if __name__ == "__main__":
    unittest.main()
