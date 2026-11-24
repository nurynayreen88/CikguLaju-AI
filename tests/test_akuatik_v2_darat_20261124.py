"""Aquatic V2 source regression; no live routing or calendar changes."""
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/"rph_standalone/pjpk/akuatik_v2_darat_t1_t6_20261124.json"
MANIFEST=ROOT/"rpt_2027/pjpk/pjpk_2027_rpt_manifest.json"

class AquaticV2Source(unittest.TestCase):
    def setUp(self):
        self.root=json.loads(SOURCE.read_text(encoding="utf-8"))
        self.records=self.root["records"]

    def test_all_years_distinct_and_not_published(self):
        self.assertEqual(self.root["status"],"QA_NOT_PUBLISHED")
        self.assertEqual(len(self.records),18)
        self.assertEqual(len({(r["year"],r["source_id"]) for r in self.records}),18)
        self.assertEqual([sum(r["year"]==y for r in self.records) for y in range(1,7)],[2,4,2,2,5,3])
        for r in self.records:
            self.assertFalse(r["ready"])
            self.assertEqual(r["variant"],"V2_DARAT")
            self.assertEqual(set(r["metadata"].values()),{""})
            self.assertTrue(all(r[k] for k in ("objective","criteria","induction","bbm","safety","pbd","closure","remedial","extension","reflection")))
            self.assertEqual(len(r["activities"]),3)
            self.assertTrue(all(a["title"] and a["body"] for a in r["activities"]))
            self.assertIn(r["criteria"],r["pbd"])
            self.assertIn("Kemahiran psikomotor di air belum ditaksir",r["pbd"])
            self.assertIn("Kemahiran dalam air belum ditaksir",r["reflection"])
            self.assertIn("Tiada kolam, rendaman, tahan nafas",r["safety"])
            self.assertIn("Aktiviti Darat",r["title"])

    def test_numbered_kssr_original_standards_unchanged(self):
        rows=json.loads(MANIFEST.read_text(encoding="utf-8"))["records"]
        for r in self.records:
            if r["year"] not in (3,4):
                continue
            original=next(x for x in rows if x["subject"]=="PJ" and x["year"]==r["year"] and x["pdp"]==int(r["source_id"]))
            s=r["source_standard_reference"]
            self.assertEqual(set(s["psychomotor"]+s["cognitive"]+s["affective"]),set(original["sp"]))
            self.assertEqual(set(s["sk"]),set(original["sk"]))
        for r in self.records:
            if r["year"] in (2,5,6):
                self.assertEqual(r["status"],"QA_SUPPLEMENT_NO_RPT_SLOT")
                self.assertFalse(r["source_id"].isdigit())

    def test_all_18_real_word_pdf(self):
        from io import BytesIO
        from docx import Document
        import fitz
        from web import akuatik_v2_rph as renderer
        for r in self.records:
            with self.subTest(year=r["year"],source_id=r["source_id"]):
                args=(r["year"],r["source_id"])
                word=renderer.render(*args,"word",qa_reference=True)
                doc=Document(BytesIO(word))
                self.assertEqual(len(doc.tables),4)
                text=" ".join(c.text for table in doc.tables for row in table.rows for c in row.cells)
                self.assertIn(r["objective"],text)
                self.assertIn(r["criteria"],text)
                for line in r["standard_descriptions"]["psychomotor"]+r["standard_descriptions"]["cognitive"]:
                    self.assertIn(line,text)
                for activity in r["activities"]:
                    self.assertIn(activity["body"],text)
                self.assertIn("Kemahiran dalam air belum ditaksir",text)
                for i in range(1,4):
                    self.assertTrue(any(run.bold and run.text.startswith(f"Aktiviti {i}") for table in doc.tables for row in table.rows for cell in row.cells for p in cell.paragraphs for run in p.runs))
                pdf=renderer.render(*args,"pdf",qa_reference=True)
                with fitz.open(stream=pdf,filetype="pdf") as pages:
                    self.assertEqual(len(pages),1,"RPH must fit a single A4 without removing content")
                    self.assertAlmostEqual(pages[0].rect.width,595.28,delta=1)
                    self.assertAlmostEqual(pages[0].rect.height,841.89,delta=1)
                    body=" ".join(pages[0].get_text().split())
                    self.assertIn("Kemahiran dalam air belum ditaksir",body)
                    self.assertIn("Aktiviti 3",body)
                    self.assertIn("Akuatik V2",body)
        for args in [(2,"999"),(5,"025"),(1,"051")]:
            with self.assertRaises(ValueError):
                renderer.resolve(*args)

    def test_only_actual_water_required_existing_pdp_has_v2(self):
        from web import akuatik_v2_rph as renderer
        expected={(1,"KP2027-A-051"),(1,"KP2027-B-050"),(3,"022"),(3,"023"),(4,"026")}
        found={(r["year"],r["source_id"]) for r in self.records if renderer.eligible_existing_pdp(r["year"],r["source_id"])}
        self.assertEqual(found,expected)
        self.assertFalse(self.root["menu_policy"]["enabled"])
        for r in self.records:
            key=(r["year"],r["source_id"])
            if key in expected:
                self.assertEqual(renderer.options(*key),("V1","V2_DARAT"))
            else:
                self.assertEqual(renderer.options(*key),("V1",))
                with self.assertRaises(ValueError):
                    renderer.render(*key,"pdf")
        for key in [(4,"001"),(2,"028"),(5,"009"),(6,"026"),(1,"KP2027-A-050")]:
            self.assertEqual(renderer.options(*key),("V1",))

    def test_protected_renderer_rejects_unlisted_and_unauthenticated(self):
        from flask import Flask
        from types import SimpleNamespace
        from unittest.mock import patch
        from web.native_rph_telegram_api import create_native_rph_blueprint
        app=Flask(__name__)
        app.register_blueprint(create_native_rph_blueprint(SimpleNamespace(
            create_word_file=lambda *a: None, create_pdf_file=lambda *a: None)))
        client=app.test_client()
        route="/internal/rph/v1/akuatik-v2/render"
        payload={"year":3,"source_id":"022","format":"pdf",
                 "teacher":{"class":"","date":"","time":"","students":""}}
        token="test-token-"+"x"*40
        headers={"Authorization":"Bearer "+token}
        with patch.dict("os.environ",{"CIKGULAJU_WEB_NATIVE_RPH_ENABLED":"1",
                                      "CIKGULAJU_AUTHORITATIVE_API_TOKEN":token}):
            self.assertEqual(client.post(route,json=payload).status_code,401)
            self.assertEqual(client.post(route,json={**payload,"year":4,"source_id":"025"},headers=headers).status_code,400)
            self.assertEqual(client.post(route,json={**payload,"qa_reference":True},headers=headers).status_code,400)
            response=client.post(route,json=payload,headers=headers)
            self.assertEqual(response.status_code,200)
            self.assertTrue(response.data.startswith(b"%PDF-"))
            self.assertIn("no-store",response.headers["Cache-Control"])
            self.assertIn("AKUATIK_V2",response.headers["Content-Disposition"])

if __name__=="__main__":
    unittest.main()
