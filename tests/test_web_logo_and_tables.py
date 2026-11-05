"""One-table Word/PDF Web output and owner-provided alpha logo regression."""
import base64
from io import BytesIO
from pathlib import Path
import re
import unittest
from unittest.mock import patch
from xml.etree import ElementTree

from docx import Document
from PIL import Image
from flask import Flask
from web.unified_rph_web import create_blueprint, source_records


ROOT = Path(__file__).resolve().parents[1]


class WebLogoAndTables(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app = Flask(__name__)
        app.register_blueprint(create_blueprint())
        cls.client = app.test_client()

    def test_logo_has_real_transparency_and_is_served_publicly(self):
        p = ROOT / "web_v1_static_preview" / "cikgulaju-logo.svg"
        root = ElementTree.parse(p).getroot()
        self.assertTrue(root.tag.endswith("svg"))
        embedded = root.find("{http://www.w3.org/2000/svg}image")
        self.assertIsNotNone(embedded)
        data = embedded.attrib["href"]
        self.assertTrue(data.startswith("data:image/webp;base64,"))
        png = Image.open(BytesIO(base64.b64decode(data.split(",",1)[1])))
        self.assertEqual(png.mode, "RGBA")
        self.assertEqual(png.getpixel((0,0))[3], 0)
        from tools.run_web_production import app
        response = app.test_client().get("/assets/cikgulaju-logo.svg")
        self.assertEqual(response.status_code, 200)
        self.assertIn("image/svg+xml", response.headers["Content-Type"])

    def test_login_and_rph_preview_use_logo_and_real_html_table(self):
        html=(ROOT / "web_v1_static_preview" / "index.html").read_text(encoding="utf8")
        self.assertIn('rel="icon" type="image/svg+xml"', html)
        self.assertIn('class="brand-icon"', html)
        self.assertIn('class="login-brand"', html)
        self.assertIn('document.createElement("table")', html)
        self.assertIn('className="rph-preview-table"', html)
        self.assertNotIn('h.textContent=field.label;p.textContent=field.value', html)

    @patch("web.unified_rph_web._has_paid_access", return_value=True)
    @patch("web.unified_rph_web._account", return_value=({"telegram_user_id": 123}, None))
    def test_real_english_lessons_y2_to_y6_are_word_tables_and_a4(self, *_):
        for year in range(2,7):
            records=source_records(year, "ENGLISH")
            self.assertEqual(len(records),160)
            for row in [records[0],records[24],records[85],records[-1]]:
                with self.subTest(year=year,lesson=row["lesson"]):
                    args={"year":year,"subject":"ENGLISH","unit":row["unit"],
                          "lesson":row["token"],"teacher_class":"4 Bestari",
                          "teacher_date":"2027-03-08","teacher_time":"09:15"}
                    preview=self.client.get("/api/web/rph/preview",query_string=args)
                    if preview.status_code==503:
                        # Some intentionally withheld SOW lessons have no approved Web mapping.
                        continue
                    self.assertEqual(preview.status_code,200,preview.get_json())
                    word=self.client.get("/api/web/rph/word",query_string=args)
                    self.assertEqual(word.status_code,200,word.get_json() if word.is_json else "")
                    document=Document(BytesIO(word.data))
                    self.assertEqual(len(document.tables),1)
                    table=document.tables[0]
                    self.assertEqual(len(table.columns),2)
                    self.assertGreater(len(table.rows),5)
                    self.assertIn("4 Bestari",table.cell(1,1).text)
                    self.assertIn("2027-03-08",table.cell(2,1).text)
                    self.assertIn("09:15",table.cell(3,1).text)
                    for field in preview.get_json()["fields"]:
                        if field["label"] and field["value"]:
                            self.assertIn(field["label"],[r.cells[0].text for r in table.rows])
                    page=document.sections[0]
                    self.assertAlmostEqual(page.page_width.cm,21.0,places=1)
                    self.assertAlmostEqual(page.page_height.cm,29.7,places=1)

    @patch("web.unified_rph_web._account", return_value=(None,({"error":"login required"},401)))
    def test_anonymous_still_cannot_download(self,*_):
        self.assertEqual(self.client.get("/api/web/rph/word").status_code,401)


if __name__ == "__main__":
    unittest.main()
