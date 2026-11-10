"""RPT catalog should not leak internal release labels into teacher-facing UI."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web_v1_static_preview" / "index.html"

class RPTTeacherLabels(unittest.TestCase):
    def test_catalog_uses_availability_not_internal_draft_status(self):
        html = HTML.read_text(encoding="utf-8")
        self.assertNotIn('status.textContent=typeof year.status', html)
        self.assertNotIn('RPT DRAF/SEPARA DRAF', html)
        self.assertIn('status.textContent=year.year===1?"Belum dibuka":year.download_enabled===true?"PDF tersedia":"Belum tersedia";', html)
        self.assertIn("Sila semak padanan SK/SP, buku teks dan takwim sekolah", html)
        self.assertIn('if(year.year===1)', html)
        self.assertIn('year.download_enabled===true', html)

if __name__ == "__main__":
    unittest.main()
