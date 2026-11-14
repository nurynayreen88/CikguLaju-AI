import unittest
from curriculum_version_telegram import install

class TelegramCurriculumTests(unittest.TestCase):
    def setUp(self):
        self.messages=[]
        self.calls=[]
        self.ns={"state":{},"send":lambda cid,text,kb:self.messages.append((text,kb)),
                 "SUBJECTS_BY_GRADE":{"Tahun 1":["Matematik","Sains","Bahasa Cina","Bahasa Tamil"],
                                      "Tahun 2":["Sains","Matematik"],"Tingkatan 1":["Bahasa Inggeris"]},
                 "SUBJECT_LABEL":{"Matematik":"Matematik","Sains":"Sains","Bahasa Inggeris":"Bahasa Inggeris"},
                 "_CIKGULAJU_DEV_SUBJECTS_V2617":{"Pendidikan Seni Visual":(1,2,3),"Sejarah":(4,5,6)},
                 "year":lambda cid,level:self.calls.append(("year",level)),
                 "subjects":lambda cid,label:self.calls.append(("subjects",label)),
                 "callback":lambda cid,d:self.calls.append(("callback",d))}
        self.assertTrue(install(self.ns))
        self.ns["state"][1] = {"task":"quick_material","quick_material_flow":True}

    def test_year_one_versions_are_in_the_same_year_menu(self):
        self.ns["year"](1,"primary")
        _, keyboard = self.messages[-1]
        self.assertEqual(keyboard[0], [
            {"text":"Tahun 1 (KP Baharu)","callback_data":"cv_year1_kp"},
            {"text":"Tahun 1 (KSSR)","callback_data":"year_1"},
        ])
        self.assertIn("year_6",str(keyboard))
        self.ns["callback"](1,"year_1")
        self.assertEqual(self.calls,[("subjects","Tahun 1")])
        self.assertEqual(self.ns["state"][1]["curriculum_version"],"existing")

    def test_kp2027_blocks_subject_and_legacy_fallback(self):
        self.ns["state"][1].update(subject="Sains",lesson_no="7",waiting="rph_date")
        self.ns["callback"](1,"cv_year1_kp")
        self.assertNotIn("lesson_no",self.ns["state"][1])
        self.assertNotIn("waiting",self.ns["state"][1])
        self.ns["callback"](1,"sub_Matematik")
        self.ns["callback"](1,"matsubmit2528")
        self.assertEqual(self.calls,[])
        self.assertIn("Tahun 1 (KP Baharu)",self.messages[-1][0])
        self.assertIn("Akan Datang",self.messages[-1][0])
        self.assertNotIn("Bahasa Cina",str(self.messages[-1][1]))
        self.assertNotIn("Bahasa Tamil",str(self.messages[-1][1]))
        self.assertIn("cv_build_0",str(self.messages[-1][1]))
        self.ns["callback"](1,"cv_build_0")
        self.assertIn("penjanaan RPH belum dibuka",self.messages[-1][0])
        self.ns["callback"](1,"cv_choose")
        self.assertIn("cv_year1_kp",str(self.messages[-1][1]))

    def test_old_year_one_kp_button_still_opens_preview(self):
        self.ns["state"][1]["year"]="Tahun 1"
        self.ns["callback"](1,"cv_kp2027")
        self.assertIn("Tahun 1 (KP Baharu)",self.messages[-1][0])

    def test_year_two_lists_dlp_with_regular_subjects(self):
        self.ns["callback"](1,"year_2")
        keys = {button["callback_data"]:button["text"] for row in self.messages[-1][1] for button in row}
        self.assertEqual(keys["sub_Sains"],"Sains")
        self.assertEqual(keys["sub_Matematik"],"Matematik")
        self.assertIn("devsub2617_Pendidikan Seni Visual",keys)
        self.assertNotIn("devsub2617_Sejarah",keys)
        for data,title,topic in (("cv_dlp_science","Science (DLP)","Observe"),
                                 ("cv_dlp_math","Mathematics (DLP)","Recognise Numbers")):
            with self.subTest(data=data):
                self.assertEqual(keys[data],title+" — Akan Datang")
                self.ns["callback"](1,data)
                msg,kb=self.messages[-1]
                self.assertIn(topic,msg)
                self.assertIn("Activity Book pp. 1–2",msg)
                self.assertIn("back_subjects",str(kb))
                self.assertNotIn("matsubmit2528",str(kb))
        self.assertNotIn("subject",self.ns["state"][1])
        self.assertEqual(self.calls,[])
        self.ns["callback"](1,"sub_Sains")
        self.assertEqual(self.calls,[("callback","sub_Sains")])

    def test_stale_dlp_button_and_other_tasks(self):
        self.ns["callback"](1,"year_3")
        self.ns["callback"](1,"cv_dlp_science")
        self.assertNotIn("Observe",self.messages[-1][0])
        self.ns["state"][1]={"task":"bbm"}
        self.ns["year"](1,"primary")
        self.ns["callback"](1,"year_2")
        self.assertEqual(self.calls,[("subjects","Tahun 3"),("year","primary"),("subjects","Tahun 2")])

    def test_other_years_preserve_old_subject_flow(self):
        self.ns["callback"](1,"year_3")
        self.assertEqual(self.calls,[("subjects","Tahun 3")])

if __name__=="__main__":
    unittest.main()
