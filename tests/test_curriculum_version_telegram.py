import json
from pathlib import Path
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

    def test_curriculum_comes_before_year(self):
        self.ns["state"][1].update(curriculum_version="existing",year="Tahun 4")
        self.ns["year"](1,"primary")
        _, keyboard = self.messages[-1]
        self.assertEqual([row[0]["text"] for row in keyboard[:3]], ["KSSR","KP27 (KP Baharu)","DLP"])
        self.assertNotIn("year_",str(keyboard))
        self.assertNotIn("year",self.ns["state"][1])
        self.ns["callback"](1,"year_1")
        self.assertEqual(self.calls,[])
        self.ns["callback"](1,"cv_primary_kssr")
        keyboard = self.messages[-1][1]
        self.assertEqual([b["callback_data"] for row in keyboard[:3] for b in row],
                         [f"year_{year}" for year in range(1,7)])
        self.ns["callback"](1,"year_1")
        self.assertEqual(self.calls,[("subjects","Tahun 1")])
        self.assertEqual(self.ns["state"][1]["curriculum_version"],"existing")

    def test_kp2027_blocks_subject_and_legacy_fallback(self):
        self.ns["state"][1].update(subject="Sains",lesson_no="7",waiting="rph_date")
        self.ns["callback"](1,"cv_primary_kp27")
        self.assertEqual(self.messages[-1][1][0],[
            {"text":"Tahun 1 (KP Baharu)","callback_data":"cv_year1_kp"}])
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
        self.assertIn("cv_year1_kp",str(self.messages[-1][1]))
        self.ns["callback"](1,"cv_year1_kp")
        self.assertIn("Tahun 1 (KP Baharu)",self.messages[-1][0])

    def test_year_two_lists_only_dlp_subjects_in_dlp(self):
        self.ns["callback"](1,"cv_primary_dlp")
        years = [row[0] for row in self.messages[-1][1][:6]]
        self.assertEqual([button["callback_data"] for button in years],
                         [f"cv_year{n}_dlp" for n in range(1,7)])
        self.assertEqual(years[0]["text"],"Tahun 1 (KP Baharu) — Dalam Penyediaan")
        self.assertEqual(years[1]["text"],"Tahun 2 — Untuk Semakan Guru")
        self.ns["callback"](1,"cv_year2_dlp")
        keys = {button["callback_data"]:button["text"] for row in self.messages[-1][1] for button in row}
        self.assertEqual(set(keys),{"cv_dlp_science","cv_dlp_math","cv_primary_dlp","home"})
        source = Path(__file__).resolve().parents[1] / "data" / "dlp_year2_review.json"
        catalog = json.loads(source.read_text(encoding="utf-8"))
        for data, code, title, count in (
            ("cv_dlp_science", "SCIENCE_DLP", "Science (DLP)", 13),
            ("cv_dlp_math", "MATH_DLP", "Mathematics (DLP)", 41),
        ):
            self.assertEqual(keys[data], f"{title} — {count} RPH")
            self.ns["callback"](1,data)
            self.assertIn("Untuk Semakan Guru",self.messages[-1][0])
            self.assertEqual(len(self.messages[-1][1]),4)
            groups = catalog[code]
            self.assertEqual(sum(len(group["lessons"]) for group in groups),count)
            for group in groups:
                callback = "cv_dlp_unit_" + group["id"]
                self.ns["callback"](1,callback)
                lesson_keys = [row[0]["callback_data"] for row in self.messages[-1][1][:-1]]
                self.assertEqual(lesson_keys,["cv_dlp_rph_" + row["id"] for row in group["lessons"]])
                for key, lesson in zip(lesson_keys,group["lessons"],strict=True):
                    self.ns["callback"](1,key)
                    msg,kb=self.messages[-1]
                    self.assertIn(lesson["title"],msg)
                    self.assertIn(lesson["references"],msg)
                    self.assertIn("Teacher:",msg)
                    self.assertIn("Pupils:",msg)
                    self.assertIn("Reflection",msg)
                    self.assertLess(len(msg),4096)
                    self.assertEqual(kb[0][0]["callback_data"],callback)
                    self.assertLessEqual(len(key.encode()),64)
                    self.assertNotIn("matsubmit2528",str(kb))
                self.ns["callback"](1,"cv_dlp_rph_DLP-UNKNOWN-Y2-U01-01")
                self.assertIn("Pilih unit",self.messages[-1][0])
                self.ns["callback"](1,data)
            self.ns["callback"](1,"back_subjects")
            self.assertIn("cv_dlp_math",str(self.messages[-1][1]))
        self.assertNotIn("subject",self.ns["state"][1])
        self.assertEqual(self.calls,[])
        self.ns["callback"](1,"sub_Sains")
        self.assertEqual(self.calls,[])
        self.ns["callback"](1,"cv_primary_kssr")
        self.ns["callback"](1,"year_2")
        self.ns["callback"](1,"sub_Sains")
        self.assertEqual(self.calls,[("subjects","Tahun 2"),("callback","sub_Sains")])

    def test_dlp_other_years_show_subject_status_without_using_year_two_preview(self):
        self.ns["callback"](1,"cv_primary_dlp")
        for n in (1,3,4,5,6):
            with self.subTest(year=n):
                self.ns["callback"](1,f"cv_year{n}_dlp")
                year_label = f"Tahun {n}" + (" (KP Baharu)" if n == 1 else "")
                self.assertIn(year_label,self.messages[-1][0])
                self.assertEqual([row[0]["text"] for row in self.messages[-1][1][:2]],
                                 ["Science (DLP) — Dalam Penyediaan","Mathematics (DLP) — Dalam Penyediaan"])
                for code in ("cv_dlp_science","cv_dlp_math"):
                    self.ns["callback"](1,code)
                    message = self.messages[-1][0]
                    self.assertIn(year_label,message)
                    self.assertIn("Dalam Penyediaan",message)
                    self.assertNotIn("Activity Book",message)
                self.ns["callback"](1,"matsubmit2528")
                self.assertEqual(self.calls,[])

    def test_stale_dlp_button_and_other_tasks(self):
        self.ns["callback"](1,"cv_primary_kssr")
        self.ns["callback"](1,"year_3")
        self.ns["callback"](1,"cv_dlp_science")
        self.assertNotIn("Observe",self.messages[-1][0])
        self.ns["state"][1]={"task":"bbm"}
        self.ns["year"](1,"primary")
        self.ns["callback"](1,"year_2")
        self.assertEqual(self.calls,[("subjects","Tahun 3"),("year","primary"),("subjects","Tahun 2")])

    def test_other_years_preserve_old_subject_flow(self):
        self.ns["callback"](1,"cv_primary_kssr")
        self.ns["callback"](1,"year_3")
        self.assertEqual(self.calls,[("subjects","Tahun 3")])

if __name__=="__main__":
    unittest.main()
