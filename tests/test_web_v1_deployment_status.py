import unittest

from tools.run_web_v1_preview import app


class DeploymentStatusTests(unittest.TestCase):
    def test_staging_not_misrepresented_as_production(self):
        response = app.test_client().get("/api/deployment/status")
        self.assertEqual(response.status_code, 200)
        status = response.get_json()
        self.assertEqual(status["environment"], "staging-preview")
        self.assertEqual(status["hosting"], "render")
        self.assertIs(status["telegram_production_separate"], True)
        self.assertIs(status["account_linked"], False)
        self.assertIs(status["rph_generation_enabled"], False)
        self.assertIs(status["public_launch_ready"], False)
        self.assertIn("no-store", response.headers["Cache-Control"])


if __name__ == "__main__":
    unittest.main()
