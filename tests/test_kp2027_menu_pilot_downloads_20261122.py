"""KP2027 Year-1 menu: use approved private download routes, never generic KSSR generation."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "web_v1_static_preview" / "index.html").read_text(encoding="utf-8")
ALAM = (ROOT / "web" / "kp2027_alam_private_web.py").read_text(encoding="utf-8")
MATH = (ROOT / "web" / "kp2027_math_canary_web.py").read_text(encoding="utf-8")

class TestPilotNavigation(unittest.TestCase):
    def test_year1_has_only_verified_subject_routes(self):
        selector = PAGE[PAGE.index('if(choice==="kp2027"){'):PAGE.index('if(choice==="sjkc"||choice==="sjkt"){')]
        self.assertIn('if(targetYear!=="1")return;', selector)
        self.assertIn('value:"MATH_KP2027"', selector)
        self.assertIn('value:"ALAM_KP2027"', selector)
        self.assertIn('showStep(subject,true)', selector)
        self.assertNotIn('akan datang.', selector)

    def test_subject_stays_on_same_page_with_private_lessons_and_download(self):
        section = PAGE[PAGE.index('subject.addEventListener("change",async()=>{'):][:2700]
        self.assertIn('if(curriculum.value==="kp2027")', section)
        self.assertIn('fetch(route+"/available"', section)
        self.assertIn('kp2027DisplayLessons()', section)
        self.assertNotIn('Buka pilihan Lesson dan Download', section)
        self.assertNotIn('window.location.assign(', section)
        self.assertIn('id="kp2027-pilot-downloads" hidden', PAGE)
        self.assertIn('id="kp2027-pilot-group" hidden disabled', PAGE)
        self.assertIn('id="kp2027-pilot-word"', PAGE)
        self.assertIn('id="kp2027-pilot-pdf"', PAGE)
        self.assertIn('MATH_KP2027:"/api/kp2027/sk/tahun-1/matematik"', PAGE)
        self.assertIn('ALAM_KP2027:"/api/kp2027/sk/tahun-1/alam-dan-manusia"', PAGE)
        self.assertIn('body:JSON.stringify(payload)', PAGE)
        self.assertIn('credentials:"same-origin"', PAGE)

    def test_pilot_downloads_still_require_private_access_and_approval(self):
        self.assertIn("CIKGULAJU_KP2027_ALAM_CANARY_ENABLED", ALAM)
        self.assertIn("CANARY_APPROVED", ALAM)
        self.assertIn("authorize_rendered_document(", ALAM)
        self.assertIn("Origin", ALAM)
        self.assertIn("CANARY_APPROVED", MATH)
        self.assertIn("authorize_rendered_document(", MATH)
        self.assertIn("Origin", MATH)
        self.assertIn("Alam dan Manusia • KP2027 Tahun 1", ALAM)

if __name__ == "__main__":
    unittest.main()
