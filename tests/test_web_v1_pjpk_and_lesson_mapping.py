"""Static regression checks: browser must not confuse RPT row IDs with lesson numbers."""
from pathlib import Path
import unittest

HTML = (Path(__file__).resolve().parents[1] / "web_v1_static_preview" / "index.html").read_text(encoding="utf-8")


class WebNavigationSafetyTests(unittest.TestCase):
    def test_pjpk_requires_explicit_component(self):
        self.assertIn('id="component" hidden disabled', HTML)
        self.assertIn('if(subject.value==="PJPK")', HTML)
        self.assertIn('extra.component=component.value', HTML)

    def test_rph_preview_binds_exact_selected_year_subject_unit_and_lesson(self):
        self.assertIn('year:year.value,subject:subject.value,unit:unit.value,lesson:lesson.value', HTML)
        self.assertIn('data.selection!==lesson.value', HTML)
        self.assertIn('data.unit!==unit.value', HTML)
        self.assertIn('data.subject!==subject.value', HTML)
        self.assertIn('"/api/web/rph/preview?"+key', HTML)
        self.assertNotIn('lesson_no:Number(lesson.value)', HTML)
        self.assertNotIn('"/api/web/english/rph"', HTML)

    def test_hidden_links_when_delivery_is_not_verified(self):
        self.assertIn('data.download_enabled===true&&item.download_enabled===true', HTML)
        self.assertIn('document.getElementById("download-all").disabled=true', HTML)


if __name__ == "__main__":
    unittest.main()
