import unittest
from curriculum_version_telegram import install

class TelegramCurriculumTests(unittest.TestCase):
    def setUp(self):
        self.messages=[]
        self.calls=[]
        self.ns={"state":{},"send":lambda cid,text,kb:self.messages.append((text,kb)),
                 "SUBJECTS_BY_GRADE":{"Tahun 1":["Matematik","Sains"],"Tingkatan 1":["Bahasa Inggeris"]},
                 "SUBJECT_LABEL":{"Matematik":"Matematik","Sains":"Sains","Bahasa Inggeris":"Bahasa Inggeris"},
                 "subjects":lambda cid,label:self.calls.append(("subjects",label)),
                 "callback":lambda cid,d:self.calls.append(("callback",d))}
        self.assertTrue(install(self.ns))

    def test_year_one_asks_curriculum_before_subject(self):
        self.ns["callback"](1,"year_1")
        self.assertEqual(self.calls,[])
        self.assertIn("cv_kp2027",str(self.messages[-1][1]))
        self.ns["callback"](1,"cv_existing")
        self.assertEqual(self.calls,[("subjects","Tahun 1")])

    def test_kp2027_blocks_subject_and_legacy_fallback(self):
        self.ns["callback"](1,"year_1")
        self.ns["callback"](1,"cv_kp2027")
        self.ns["callback"](1,"sub_Matematik")
        self.assertEqual(self.calls,[])
        self.assertIn("Dalam Pembinaan",self.messages[-1][0])
        self.assertIn("cv_build_0",str(self.messages[-1][1]))
        self.ns["callback"](1,"cv_build_0")
        self.assertIn("penjanaan RPH belum dibuka",self.messages[-1][0])

    def test_other_years_preserve_old_subject_flow(self):
        self.ns["callback"](1,"year_3")
        self.assertEqual(self.calls,[("subjects","Tahun 3")])

if __name__=="__main__":
    unittest.main()
