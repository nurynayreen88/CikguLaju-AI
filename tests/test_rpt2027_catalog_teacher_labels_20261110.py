"""RPT catalog should not leak internal release labels into teacher-facing UI."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "web_v1_static_preview" / "index.html"

class RPTTeacherLabels(unittest.TestCase):
    def test_catalog_uses_availability_not_internal_draft_status(self):
        html = HTML.read_text(encoding="utf-8")
        rpt = html.split('<section id="rpt2027-panel"', 1)[1].split("</section>", 1)[0]
        selectors = ['id="rpt-curriculum"', 'id="rpt-year"', 'id="rpt-subject"']
        positions = [rpt.index(selector) for selector in selectors]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn('rpt-all-list', rpt)
        self.assertIn("Semak padanan SK/SP, buku teks dan takwim sekolah", rpt)
        logic = html.split("function rptCurriculumFor(", 1)[1].split("teacherClass.addEventListener", 1)[0]
        self.assertNotIn("year.status", logic)
        self.assertIn("Dalam Penyediaan", logic)
        self.assertIn("Akses berbayar", logic)
        self.assertIn("year.download_enabled===true", logic)

if __name__ == "__main__":
    unittest.main()
