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
        self.assertIn('kp2027DisplayUnits()', section)
        self.assertIn('function kp2027DisplayPdps()', PAGE)
        self.assertIn('if(curriculum.value==="kp2027"){kp2027DisplayPdps();return;}', PAGE)
        self.assertIn('label:"PdP "+String(e.no).padStart(3,"0")+" — "+e.tajuk+" • SP "+e.sp', PAGE)
        self.assertIn('Pilih Unit / Kandungan', PAGE)
        self.assertIn('kp2027ValidEntries(data.items.A,data.groups.A,125)', PAGE)
        self.assertIn('kp2027ValidEntries(data.items,data.lessons,64)', PAGE)
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
        self.assertIn('id="teacher-info" hidden', PAGE)
        self.assertIn('id="teacher-class"', PAGE)
        self.assertIn('id="teacher-date"', PAGE)
        self.assertIn('id="teacher-time-start"', PAGE)
        self.assertIn('id="teacher-time-end"', PAGE)
        self.assertIn('id="teacher-students"', PAGE)
        self.assertIn('id="teacher-reflection-mode"', PAGE)
        self.assertIn('id="show-materials"', PAGE)
        self.assertIn('function kp2027TeacherPayload()', PAGE)
        self.assertIn('function populateKp2027MaterialList()', PAGE)
        self.assertIn('if(curriculum.value==="kp2027")populateKp2027MaterialList();', PAGE)
        self.assertIn('document.getElementById("teacher-info").hidden=!(canSelectRph()||curriculum.value==="kp2027")', PAGE)
        self.assertIn('credentials:"same-origin"', PAGE)
        self.assertIn('personalize_approved_rph', ALAM)
        self.assertIn('personalize_approved_rph', MATH)

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
