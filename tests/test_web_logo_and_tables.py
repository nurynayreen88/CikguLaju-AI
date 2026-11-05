"""Logo transparency and Telegram-parity 3-table RPH Web regression."""
import base64
from io import BytesIO
from pathlib import Path
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from docx import Document
from PIL import Image
from flask import Flask
from web.unified_rph_web import create_blueprint, source_records

ROOT=Path(__file__).resolve().parents[1]


class WebLogoAndTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app=Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client=app.test_client()

    def test_logo_has_transparency_and_is_served_publicly(self):
        path=ROOT/"web_v1_static_preview"/"cikgulaju-logo.svg"
        root=ElementTree.parse(path).getroot()
        embedded=root.find("{http://www.w3.org/2000/svg}image")
        self.assertIsNotNone(embedded)
        data=embedded.attrib["href"]
        self.assertTrue(data.startswith("data:image/webp;base64,"))
        png=Image.open(BytesIO(base64.b64decode(data.split(",",1)[1])))
        self.assertEqual(png.mode,"RGBA")
        self.assertEqual(png.getpixel((0,0))[3],0)
        from tools.run_web_production import app
        res=app.test_client().get("/assets/cikgulaju-logo.svg")
        self.assertEqual(res.status_code,200)
        self.assertIn("image/svg+xml",res.headers["Content-Type"])

    def test_browser_preview_uses_three_real_tables_and_source_contract(self):
        html=(ROOT/"web_v1_static_preview"/"index.html").read_text("utf8")
        self.assertIn('class="brand-icon"',html)
        self.assertIn('class="login-brand"',html)
        self.assertIn('style!=="telegram-native-rph-v1"',html)
        self.assertIn("rph-telegram-info",html)
        self.assertIn("rph-telegram-phases",html)
        self.assertIn("rph-telegram-footer",html)
        self.assertIn("rph-telegram-paper",html)
        self.assertIn("rph-print-footer",html)
        self.assertIn('window.print()',html)

    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":123},None))
    def test_real_english_lessons_y2_to_y6_have_exact_three_word_tables(self,*_):
        tested=0
        for year in range(2,7):
            records=source_records(year,"ENGLISH")
            self.assertEqual(len(records),160)
            for row in (records[0],records[24],records[85],records[-1]):
                with self.subTest(year=year,lesson=row["lesson"]):
                    query={"year":year,"subject":"ENGLISH","unit":row["unit"],
                           "lesson":row["token"],"teacher_class":"4 Bestari",
                           "teacher_date":"2027-03-08","teacher_time":"09:15"}
                    preview=self.client.get("/api/web/rph/preview",query_string=query)
                    if preview.status_code==503:
                        self.assertIn(preview.get_json().get("code"),
                                      ("RPH_SOURCE_NOT_VERIFIED","RPH_TELEGRAM_LAYOUT_INCOMPLETE"))
                        continue
                    self.assertEqual(preview.status_code,200,preview.get_json())
                    result=preview.get_json()
                    layout=result["telegram_layout"]
                    self.assertEqual(layout["style"],"telegram-native-rph-v1")
                    self.assertEqual(len(layout["activity_header"]),3)
                    self.assertEqual(len(layout["phases"]),3)
                    word=self.client.get("/api/web/rph/word",query_string=query)
                    self.assertEqual(word.status_code,200)
                    doc=Document(BytesIO(word.data))
                    self.assertEqual(len(doc.tables),3)
                    info,activity,followup=doc.tables
                    self.assertEqual(len(info.columns),2)
                    self.assertEqual(len(activity.columns),3)
                    self.assertEqual(len(followup.columns),2)
                    self.assertEqual(len(info.rows),len(layout["header"]))
                    self.assertEqual(len(activity.rows),4)
                    self.assertEqual(len(followup.rows),2)
                    for number,field in enumerate(layout["header"]):
                        self.assertEqual(info.cell(number,0).text,field["label"])
                        self.assertEqual(info.cell(number,1).text,field["value"])
                    for index,phase in enumerate(layout["phases"],1):
                        self.assertEqual(activity.cell(index,0).text,phase["label"])
                        self.assertEqual(activity.cell(index,1).text,phase["activity"])
                        self.assertEqual(activity.cell(index,2).text,phase["notes"] or " ")
                    self.assertIn("4 Bestari",[r.cells[1].text for r in info.rows])
                    self.assertIn("2027-03-08",[r.cells[1].text for r in info.rows])
                    self.assertIn("09:15",[r.cells[1].text for r in info.rows])
                    self.assertEqual(layout["header"][3]["value"],"Monday")
                    self.assertAlmostEqual(doc.sections[0].page_width.cm,21.0,places=1)
                    self.assertAlmostEqual(doc.sections[0].page_height.cm,29.7,places=1)
                    self.assertLess(doc.sections[0].top_margin.cm,1.0)
                    self.assertIn("CikguLaju AI",doc.sections[0].footer.paragraphs[0].text)
                    tested+=1
        self.assertGreaterEqual(tested,12)

    @patch("web.unified_rph_web._has_paid_access",return_value=True)
    @patch("web.unified_rph_web._account",return_value=({"telegram_user_id":123},None))
    def test_moral_pjpk_use_same_3_table_template_not_generic_lesson(self,*_):
        for year,subject,component in ((2,"MORAL",None),(3,"PJPK","PJ"),(4,"PJPK","PK")):
            records=source_records(year,subject,component)
            self.assertTrue(records)
            entry=records[0]
            query={"year":year,"subject":subject,"unit":entry["unit"],"lesson":entry["token"]}
            if component: query["component"]=component
            with self.subTest(subject=subject,year=year):
                response=self.client.get("/api/web/rph/preview",query_string=query)
                self.assertEqual(response.status_code,200,response.get_json())
                layout=response.get_json()["telegram_layout"]
                self.assertNotEqual(layout["phases"][1]["activity"],"—")
                self.assertEqual(layout["activity_header"],
                                 ["Fasa / Masa","Aktiviti Pengajaran & Pembelajaran","Catatan"])
                word=self.client.get("/api/web/rph/word",query_string=query)
                self.assertEqual(word.status_code,200)
                self.assertEqual(len(Document(BytesIO(word.data)).tables),3)

    @patch("web.unified_rph_web._account",return_value=(None,({"error":"login required"},401)))
    def test_anonymous_cannot_download(self,*_):
        self.assertEqual(self.client.get("/api/web/rph/word").status_code,401)


if __name__=="__main__":
    unittest.main()
