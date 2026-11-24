"""BM SK Year 1 KP2027: 353 RPH tied exactly to published RPT, Web paid/trial QA."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
from unittest import TestCase
from unittest.mock import patch

from flask import Flask

from web import kp2027_bm_rpt_aligned as bm
from web import kp2027_bm_rph_web as web

ROOT=Path(__file__).resolve().parents[1]


class TestBmKp2027Rph(TestCase):
    def test_353_rph_source_integrity_and_group_assignment(self):
        self.assertTrue(bm.ready())
        self.assertEqual(bm.COUNTS,{"A":178,"B":175})
        raw=json.loads(bm.SOURCE.read_text("utf-8"))
        for group,count in bm.COUNTS.items():
            self.assertEqual(len(raw["records"][group]),count)
            for n in range(1,count+1):
                rec=bm.lesson(group,n)
                self.assertEqual(rec["lesson"],n)
                self.assertEqual(rec["group"],group)
                self.assertRegex(rec["sp_code"],r"^[1-4]\.\d\.\d$")
                self.assertIn(rec["sp_code"],rec["sp_code"]+" "+rec["sp"])
                self.assertTrue(rec["sk"] and rec["sk_code"])
                self.assertTrue(rec["week"].startswith("M"))
                self.assertEqual(len(rec["activities"]),3)
                self.assertTrue(rec["objective"] and rec["criteria"])
                self.assertTrue(rec["remedial"] and rec["extension"])
        self.assertEqual(sum(bm.COUNTS.values()),353)

    def test_published_dk_sk_labels_preserve_all_353_original_records(self):
        raw=json.loads(bm.SOURCE.read_text("utf-8"))
        counts={"3.2":0,"4.1":0}
        updated={"3.2":"Membaca dan memahami pelbagai maklumat penting secara jelas dan tepat.",
                 "4.1":"Menulis ayat secara mekanis dengan betulnya dan kemasnya."}
        codes=set()
        for group,count in bm.COUNTS.items():
            for n in range(1,count+1):
                original=raw["records"][group][str(n)]
                actual=bm.lesson(group,n)
                codes.add(actual["sp_code"])
                if original["sk_code"] in updated:
                    counts[original["sk_code"]]+=1
                    self.assertEqual({**actual,"activities":original["activities"]},{**original,"sk":updated[original["sk_code"]]})
                else:
                    self.assertEqual({**actual,"activities":original["activities"]},original)
        self.assertEqual(counts,{"3.2":69,"4.1":41})
        self.assertEqual(len(codes),26)
        self.assertEqual(bm.approved_source(),raw["records"])

    def test_corrected_sk_appears_in_word_and_pdf(self):
        import fitz
        from docx import Document
        for code in ("3.2","4.1"):
            n=next(n for n in range(1,bm.COUNTS["A"]+1)
                   if bm.lesson("A",n)["sk_code"]==code)
            expected=bm.lesson("A",n)["sk"]
            word=Document(BytesIO(bm.render("A",n,"word",{})))
            self.assertTrue(any(expected in cell.text for t in word.tables
                               for row in t.rows for cell in row.cells))
            with fitz.open(stream=bm.render("A",n,"pdf",{}),filetype="pdf") as pdf:
                text=" ".join(" ".join(p.get_text().split()) for p in pdf)
                self.assertIn(expected,text)

    def test_reviewed_activity_order_all_353_and_no_unavailable_textbook(self):
        raw=json.loads(bm.SOURCE.read_text("utf-8"))["records"]
        changed={"A":0,"B":0}
        for group,count in bm.COUNTS.items():
            for n in range(1,count+1):
                original=raw[group][str(n)]
                actual=bm.lesson(group,n)
                preferred=raw["A"][str(bm._ACTIVITY_ORDER_ANCHORS[actual["sp_code"]])]["activities"]
                self.assertEqual(actual["activities"],preferred)
                self.assertCountEqual(actual["activities"],original["activities"])
                changed[group]+=int(actual["activities"]!=original["activities"])
                for key in ("activities","induction","criteria","material","pbd","closure","remedial","extension"):
                    value=actual[key]
                    text=" ".join(value) if isinstance(value,list) else value
                    self.assertNotRegex(text.lower(),r"buku teks|buku aktiviti|halaman|muka surat|textbook|workbook|page\\s+\\d")
        self.assertEqual(changed,{"A":111,"B":109})
        self.assertEqual(bm.approved_source(),raw)

    def test_unmatched_activity_source_is_never_replaced(self):
        raw=bm.approved_source()
        original={**raw["A"]["8"],"activities":["A new teacher-led activity","Different guided practice","New independent exercise"]}
        self.assertIs(bm._ordered_activities(original,raw),original)

    def test_rph_word_pdf_and_teacher_metadata(self):
        import fitz
        from docx import Document
        for group,n in (("A",1),("A",89),("A",178),("B",1),("B",175)):
            fields={"teacher_class":"1 Bestari","teacher_date":"2027-03-02",
                    "teacher_start":"08:00","teacher_end":"09:00",
                    "teacher_students":"30","reflection_mode":"auto"}
            record=bm.lesson(group,n)
            for fmt in ("word","pdf"):
                with self.subTest(group=group,n=n,fmt=fmt):
                    payload=bm.render(group,n,fmt,fields)
                    self.assertGreater(len(payload),12000)
                    if fmt=="word":
                        self.assertTrue(payload.startswith(b"PK\x03\x04"))
                        d=Document(BytesIO(payload))
                        text=" ".join([p.text for p in d.paragraphs]+[c.text for t in d.tables for row in t.rows for c in row.cells])
                    else:
                        self.assertTrue(payload.startswith(b"%PDF-"))
                        pdf=fitz.open(stream=payload,filetype="pdf")
                        try:
                            self.assertLessEqual(pdf.page_count,2)
                            text=" ".join(p.get_text() for p in pdf)
                        finally:pdf.close()
                    for important in ("RANCANGAN PENGAJARAN HARIAN",record["sp_code"],
                                      record["sk_code"],"Aktiviti 1","Aktiviti 2","Aktiviti 3",
                                      "Pemulihan","Pengayaan","30","1 Bestari","02/03/2027"):
                        self.assertIn(important,text)

    def test_bm_printed_reflection_only_without_web_controls_or_internal_footer(self):
        from docx import Document
        import fitz
        for fmt in ("word", "pdf"):
            with self.subTest(format=fmt):
                data=bm.render("A",1,fmt,{})
                if fmt=="word":
                    doc=Document(BytesIO(data))
                    cells=[cell.text for tab in doc.tables for row in tab.rows for cell in row.cells]
                    self.assertEqual(cells.count("Refleksi"),1)
                    text=" ".join([p.text for p in doc.paragraphs]+cells)
                else:
                    pdf=fitz.open(stream=data,filetype="pdf")
                    try:
                        text=" ".join(page.get_text() for page in pdf)
                    finally:
                        pdf.close()
                from unicodedata import normalize
                text=re.sub(r"\s+"," ",normalize("NFKC",text))  # Normalize PDF ligatures and wrapped labels.
                for forbidden in ("Refleksi (Auto / Manual)", "SEMAKAN PELAKSANAAN",
                                  "RPT M", "CIKGULAJU • KP2027"):
                    self.assertNotIn(forbidden,text)
                for required in ("Standard Pembelajaran", "Aktiviti 1", "Pemulihan",
                                 "Pengayaan", "Refleksi"):
                    self.assertIn(required,text)

    def test_reported_b16_uses_canonical_header_and_equal_table_widths(self):
        from docx import Document
        import fitz
        rec=bm.lesson("B",16)
        d=Document(BytesIO(bm.render("B",16,"word",{})))
        head,body=d.tables
        self.assertEqual(sum(c.width for c in head.rows[0].cells),
                         sum(c.width for c in body.rows[0].cells))
        self.assertEqual(head.cell(0,0).text.splitlines(),[
            "BAHASA MELAYU SK","Tahun 1","Tajuk: "+rec["title"],"Kandungan: "+rec["unit"]])
        self.assertNotIn("Kumpulan",head.cell(0,0).text)
        self.assertNotRegex(head.cell(0,0).text,r"PdP\s+\d+")
        self.assertIn("Maklumat PdP",head.cell(0,1).text)
        self.assertIn("Bil. Murid:",head.cell(0,1).text)
        self.assertEqual(d.styles["Normal"].font.name,"Times New Roman")
        self.assertIn("DBE8F5",head.cell(0,0)._tc.xml)
        self.assertIn("EDF3FA",body.cell(0,0)._tc.xml)
        with fitz.open(stream=bm.render("B",16,"pdf",{}),filetype="pdf") as pdf:
            self.assertEqual(pdf.page_count,1)
            page=pdf[0]
            subject=page.search_for("BAHASA MELAYU SK")[0]
            teacher=page.search_for("Maklumat PdP")[0]
            self.assertLess(subject.x0,teacher.x0)
            self.assertLess(abs(subject.y0-teacher.y0),15)
            text=" ".join(page.get_text().split())
            self.assertNotRegex(text,r"PdP\s+\d+")
            self.assertNotIn("Kumpulan B",text)
            self.assertIn("Tajuk: "+rec["title"],text)
            self.assertIn("Kandungan: "+rec["unit"],text)
            self.assertIn(rec["sp_code"],text)
            self.assertIn(rec["criteria"],text)
            for activity in rec["activities"]:
                self.assertIn(activity,text)

    def test_invalid_group_lesson_format_and_teacher_payload_rejected(self):
        for group,n in (("C",1),("A",179),("B",176),("B",0),("A","1")):
            with self.subTest(group=group,n=n),self.assertRaises(bm.Unavailable):
                bm.lesson(group,n)
        with self.assertRaises(bm.Unavailable):
            bm.render("A",1,"zip")
        from web.kp2027_pilot_teacher_fields import TeacherFieldError
        with self.assertRaises(TeacherFieldError):
            bm.render("A",1,"pdf",{"teacher_students":"-200"})

    def test_website_auth_download_and_trial_gate(self):
        app=Flask("kp2027_bm_rph_tests")
        app.config["TESTING"]=True
        app.register_blueprint(web.create_blueprint())
        c=app.test_client()
        r=c.get("/api/kp2027/sk/tahun-1/bahasa-melayu-sk/available")
        self.assertEqual(r.status_code,503)
        with (patch.object(web,"_config",return_value={
                    "account_backend":"supabase","CIKGULAJU_WEB_SESSION_SECRET":"s"*40,
                    "supabase_url":"https://example.supabase.co","supabase_key":"unused"}),
              patch.object(web,"verify_session_ticket",return_value=42),
              patch.object(web,"_lookup",return_value={"telegram_user_id":42,"authenticated":True,
                           "free_remaining":10,"rakan_pembangun":True})):
            r=c.get("/api/kp2027/sk/tahun-1/bahasa-melayu-sk/available")
            self.assertEqual(r.status_code,200)
            data=r.get_json()
            self.assertEqual(len(data["groups"]["A"]),178)
            self.assertEqual(len(data["groups"]["B"]),175)
            self.assertEqual(len(data["items"]["A"]),178)
            self.assertEqual(len(data["items"]["B"]),175)
            self.assertEqual(data["academic_status"],"SEMAKAN PELAKSANAAN")
            url="/api/kp2027/sk/tahun-1/bahasa-melayu-sk/download"
            body={"group":"A","lesson":1,"format":"pdf"}
            self.assertEqual(c.post(url,json=body).status_code,403)
            valid=c.post(url,json=body,headers={"Origin":"https://cikgulaju-web.onrender.com"})
            self.assertEqual(valid.status_code,200)
            self.assertIn("application/pdf",valid.headers["Content-Type"])
            self.assertTrue(valid.data.startswith(b"%PDF-"))
            self.assertEqual(valid.headers["X-RPH-QA-Status"],"SEMAKAN-PELAKSANAAN")
            self.assertNotIn("X-RPH-Trial-Remaining",valid.headers)
        with (patch.object(web,"_config",return_value={
                    "account_backend":"supabase","CIKGULAJU_WEB_SESSION_SECRET":"s"*40,
                    "supabase_url":"https://example.supabase.co","supabase_key":"unused"}),
              patch.object(web,"verify_session_ticket",return_value=42),
              patch.object(web,"_lookup",return_value={"telegram_user_id":42,"authenticated":True,
                           "free_remaining":0,"rakan_pembangun":False})):
            denied=c.post(url,json=body,headers={"Origin":"https://cikgulaju-web.onrender.com"})
            self.assertEqual(denied.status_code,403)
            self.assertEqual(denied.get_json()["code"],"FREE_TRIAL_EXHAUSTED")

    def test_menu_uses_existing_teacher_info_and_rph_buttons(self):
        html=(ROOT/"web_v1_static_preview/index.html").read_text("utf-8")
        self.assertIn('value:"BM_SK_KP2027",label:"Bahasa Melayu SK (KP2027)"',html)
        self.assertIn('/api/kp2027/sk/tahun-1/bahasa-melayu-sk',html)
        self.assertIn('["MATH_KP2027","BM_SK_KP2027","PJ_KP2027"].includes(code)',html)
        self.assertIn('kp2027TeacherPayload()',html)
        self.assertIn('kp2027DownloadApproved(format)',html)
        self.assertIn('KP2027',html)
        app=(ROOT/"tools/run_web_production.py").read_text("utf-8")
        self.assertIn('create_kp2027_bm_rph()',app)


if __name__=="__main__":
    import unittest
    unittest.main()
