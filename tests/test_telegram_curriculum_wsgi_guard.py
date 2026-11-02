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

    def test_valid_staging_registers_read_only_blueprint_with_mocked_runtime(self):
        # A stub runtime avoids importing app.py, starting a bot, or opening DB.
        script = """
import sys
import types
import importlib
fake_app = types.ModuleType("app")
class StubFlask:
    def __init__(self):
        self.blueprints = []
    def register_blueprint(self, bp):
        self.blueprints.append(bp)
fake_app.app = StubFlask()
fake_app.DB_PATH = "/nonexistent/staging-only.db"
fake_app.CIKGULAJU_DB_V2600_ACTIVE = True
sys.modules["app"] = fake_app
fake_web = types.ModuleType("web.telegram_curriculum_api")
def create_curriculum_blueprint(provider):
    assert provider() == "/nonexistent/staging-only.db"
    return "read-only-curriculum-blueprint"
fake_web.create_curriculum_blueprint = create_curriculum_blueprint
sys.modules["web.telegram_curriculum_api"] = fake_web
entry = importlib.import_module("tools.run_telegram_curriculum_wsgi")
assert entry.app.blueprints == ["read-only-curriculum-blueprint"]
"""
        env = os.environ.copy()
        env.update({
            "CIKGULAJU_ENV": "staging",
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 32,
        })
        result = subprocess.run(
            [sys.executable, "-c", script], env=env,
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_valid_staging_rejects_inactive_primary_database(self):
        script = """
import sys
import types
import importlib
fake_app = types.ModuleType("app")
class StubFlask:
    def register_blueprint(self, bp):
        pass
fake_app.app = StubFlask()
fake_app.DB_PATH = "/nonexistent/staging-only.db"
fake_app.CIKGULAJU_DB_V2600_ACTIVE = False
sys.modules["app"] = fake_app
fake_web = types.ModuleType("web.telegram_curriculum_api")
def create_curriculum_blueprint(provider):
    assert provider() is None, "inactive master must fail closed"
    return object()
fake_web.create_curriculum_blueprint = create_curriculum_blueprint
sys.modules["web.telegram_curriculum_api"] = fake_web
importlib.import_module("tools.run_telegram_curriculum_wsgi")
"""
        env = os.environ.copy()
        env.update({
            "CIKGULAJU_ENV": "staging",
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 32,
        })
        result = subprocess.run(
            [sys.executable, "-c", script], env=env,
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_active_database_path_tracks_runtime_changes(self):
        script = """
import sys
import types
import importlib
fake_app = types.ModuleType("app")
class StubFlask:
    def register_blueprint(self, bp):
        pass
fake_app.app = StubFlask()
fake_app.DB_PATH = "/tmp/master-a.db"
fake_app.CIKGULAJU_DB_V2600_ACTIVE = True
sys.modules["app"] = fake_app
fake_web = types.ModuleType("web.telegram_curriculum_api")
def create_curriculum_blueprint(provider):
    fake_app.DB_PATH = "/tmp/master-b.db"
    assert provider() == "/tmp/master-b.db", "must read current runtime path"
    fake_app.CIKGULAJU_DB_V2600_ACTIVE = False
    assert provider() is None, "must fail closed after runtime fallback"
    return object()
fake_web.create_curriculum_blueprint = create_curriculum_blueprint
sys.modules["web.telegram_curriculum_api"] = fake_web
importlib.import_module("tools.run_telegram_curriculum_wsgi")
"""
        env = os.environ.copy()
        env.update({
            "CIKGULAJU_ENV": "staging",
            "CIKGULAJU_CURRICULUM_API_ENABLED": "1",
            "CIKGULAJU_AUTHORITATIVE_API_TOKEN": "x" * 32,
        })
        result = subprocess.run(
            [sys.executable, "-c", script], env=env,
            capture_output=True, text=True, timeout=15,
        )
        self.assertEqual(result.returncode, 0, result.stderr)

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
