"""Production Web carries latest repo source files without publishing draft lessons."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class ProductionSourceInventory(unittest.TestCase):
    def test_independent_web_entrypoint(self):
        from tools.run_web_production import app
        client=app.test_client()
        r=client.get("/healthz")
        self.assertEqual(r.status_code,200)
        self.assertEqual(r.get_json()["service"],"cikgulaju-web")
        self.assertEqual(client.get("/api/web/teacher/classes").status_code,503 if __import__('web_v1_telegram_auth_routes')._config() is None else 401)
        self.assertIn("/api/web/rph/preview",{r.rule for r in app.url_map.iter_rules()})
        self.assertIn("/api/web/rph/word",{r.rule for r in app.url_map.iter_rules()})
        self.assertIn("/api/web/rph/pdf",{r.rule for r in app.url_map.iter_rules()})

    def test_main_source_files_retained(self):
        from web.unified_rph_web import source_records
        for year in range(2,7):
            with self.subTest(year=year):
                self.assertEqual(len(source_records(year,"ENGLISH")),160)
                self.assertEqual(len(source_records(year,"PSV")),42)
                self.assertEqual(len(list((ROOT/"rph_standalone"/"psv"/f"year{year}").glob("lesson_*.md"))),42)
        from rph_standalone.pendidikan_islam_draf_2027.pi_review_catalog import counts
        self.assertEqual(counts(),{"total":696,"draf":690,"held":6,"ready":0})

    def test_unapproved_sources_remain_unapproved(self):
        from web.unified_rph_web import source_records
        for year in range(2,7):
            self.assertTrue(all(r["path"] is None for r in source_records(year,"PSV")))
        self.assertEqual((ROOT/"rph_standalone"/"matematik"/"staging_preview.py").is_file(),True)

    def test_psv_release_is_independently_approval_gated(self):
        from unittest.mock import patch
        from web.unified_rph_web import source_records
        # Even a mistakenly enabled approval switch cannot publish DRAF rows.
        with patch("web.unified_rph_web._psv_release_approved", return_value=True):
            for year in range(2,7):
                records=source_records(year,"PSV")
                self.assertEqual(len(records),42)
                self.assertTrue(all(rec["path"] is None for rec in records))
                self.assertTrue(all(rec["status"] != "READY" for rec in records))

    def test_public_branding(self):
        html=(ROOT/"web_v1_static_preview"/"index.html").read_text(encoding="utf8")
        self.assertIn("CikguLaju AI · Web",html)
        self.assertNotIn("Web staging",html)
        self.assertNotIn('id="rph-preview-button"',html)
        self.assertIn('id="rph-word"',html)
        self.assertIn('id="rph-pdf"',html)

if __name__=="__main__":
    unittest.main()
