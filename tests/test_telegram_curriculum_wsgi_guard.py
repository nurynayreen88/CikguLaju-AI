"""Safety regression tests for isolated Telegram curriculum WSGI.

These tests deliberately avoid importing Telegram app.py: an unsafe entrypoint
must reject the process before the import is attempted.
Run: python -m unittest tests.test_telegram_curriculum_wsgi_guard
"""
import os
import subprocess
import sys
import unittest


class CurriculumWsgiStartupGuardTests(unittest.TestCase):
    def run_import(self, overrides):
        env = os.environ.copy()
        for name in ("CIKGULAJU_ENV", "CIKGULAJU_CURRICULUM_API_ENABLED",
                     "CIKGULAJU_AUTHORITATIVE_API_TOKEN"):
            env.pop(name, None)
        env.update(overrides)
        return subprocess.run(
            [sys.executable, "-c",
             "import tools.run_telegram_curriculum_wsgi"],
            env=env, capture_output=True, text=True, timeout=15,
        )

    def test_missing_staging_flag_rejected_before_app_import(self):
        result = self.run_import({
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 32,
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("isolated staging environment", result.stderr)

    def test_disabled_api_rejected_before_app_import(self):
        result = self.run_import({
            "CIKGULAJU_ENV": "staging",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 32,
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("explicitly enabled", result.stderr)

    def test_weak_token_rejected_before_app_import(self):
        result = self.run_import({
            "CIKGULAJU_ENV": "staging",
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "short",
        })
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("at least 32 characters", result.stderr)


if __name__ == "__main__":
    unittest.main()
