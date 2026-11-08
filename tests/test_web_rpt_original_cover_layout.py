"""Inspect all 56 REAL GitHub RPT PDFs; accept only original cover templates.

The existing logo rectangle, school underline, teacher underline and labels
must match the layout exactly. Layout source SHA must match the immutable
RPT2027 paid catalog. Zero modification of PDFs or user database.
"""
from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path

from fitz import open as open_pdf

ROOT=Path(__file__).resolve().parents[1]/"rpt_2027"/"web_2027_pdfs"
FIELDS=("LOGO SEKOLAH","NAMA SEKOLAH","NAMA GURU")
UNDERLINES="__________________________________________"


class ExistingCoverLayoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.manifest=json.loads((ROOT/"manifest.json").read_text("utf-8"))
        cls.layout=json.loads((ROOT/"original_cover_layout_verified.json").read_text("utf-8"))

    def test_original_56_signed_templates_are_not_remapped(self):
        layout=self.layout
        manifest=self.manifest
        self.assertEqual(manifest["count"],56)
        self.assertEqual(layout["version"],1)
        self.assertEqual(layout["status"],"ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256")
        self.assertEqual(set(layout["source_sha256_by_subject_year"]),set(manifest["files"]))
        self.assertEqual(len(layout["source_sha256_by_subject_year"]),56)
        for key,e in manifest["files"].items():
            with self.subTest(key=key):
                self.assertEqual(layout["source_sha256_by_subject_year"][key],e["sha256"])
                raw=(ROOT/e["path"]).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(),e["sha256"])
                with open_pdf(stream=raw,filetype="pdf") as pdf:
                    self.assertEqual(len(pdf),e["pages"])
                    page=pdf[0]
                    self.assertAlmostEqual(page.rect.width,layout["page_width"],delta=layout["tolerance_pt"])
                    self.assertAlmostEqual(page.rect.height,layout["page_height"],delta=layout["tolerance_pt"])
                    spans=[s for block in page.get_text("dict")["blocks"]
                           if "lines" in block for line in block["lines"]
                           for s in line["spans"]]
                    labels={s["text"]:[round(x,2) for x in s["bbox"]]
                            for s in spans if s["text"] in FIELDS}
                    self.assertEqual(set(labels),set(FIELDS))
                    lines=[s for s in spans if s["text"]==UNDERLINES]
                    self.assertEqual(len(lines),2)
                    for label,ideal in [
                        ("LOGO SEKOLAH",(385.27,129.66,456.62,138.66)),
                        ("NAMA SEKOLAH",(106.94,340.4,197.04,350.4)),
                        ("NAMA GURU",(106.94,396.4,176.44,406.4)),
                    ]:
                        self.assertTrue(all(abs(a-b)<2 for a,b in zip(labels[label],ideal)),
                                        (key,label,labels[label]))
                    school,teacher=[l["bbox"] for l in lines]
                    for box,ideal in [
                        (school,layout["school_underscores_top_left"]),
                        (teacher,layout["teacher_underscores_top_left"]),
                    ]:
                        self.assertTrue(all(abs(a-b)<2 for a,b in zip(box,ideal)),
                                        (key,box,ideal))
                    drawings=page.get_drawings()
                    for expected in (
                        layout["logo_frame_top_left"],
                        layout["identity_panel_top_left"],
                    ):
                        self.assertTrue(any(
                            all(abs(a-b)<0.6 for a,b in zip(shape["rect"],expected))
                            for shape in drawings
                        ),(key,expected))
                    self.assertTrue(all(
                        layout["identity_panel_top_left"][0]<field[0]<field[2]<
                        layout["identity_panel_top_left"][2]
                        for field in (layout["school_row_top_left"],
                                      layout["teacher_row_top_left"])
                    ))

    def test_ten_islamic_arabic_pdf_tables_are_rtl_other_46_stay_ltr(self):
        headers=("MINGGU / TARIKH","UNIT / TAJUK / PDP",
                 "SK","SP","CATATAN / BAHAN")
        rtl_subjects={"pendidikan_islam","bahasa_arab"}
        pdp_counts={
            "pendidikan_islam":{2:112,3:147,4:151,5:143,6:143},
            "bahasa_arab":{2:60,3:60,4:58,5:60,6:60}
        }
        rtl_count=0
        arab_links=0
        for key,entry in self.manifest["files"].items():
            subject,year_s=key.split(":")
            year=int(year_s)
            with self.subTest(key=key),open_pdf(ROOT/entry["path"]) as pdf:
                spans=[]
                for block in pdf[1].get_text("dict")["blocks"]:
                    for line in block.get("lines",[]):
                        for span in line["spans"]:
                            if span["text"].strip() in headers and 40<span["bbox"][1]<95:
                                spans.append((span["text"].strip(),span["bbox"][0]))
                positions=dict(spans)
                self.assertEqual(set(positions),set(headers))
                order=[positions[h] for h in headers]
                if subject in rtl_subjects:
                    self.assertEqual(order,sorted(order,reverse=True),
                                     "Jadual Arab/Jawi mesti RTL, Minggu paling kanan")
                    rtl_count+=1
                    tags=[]
                    for page in list(pdf)[1:]:
                        for block in page.get_text("dict")["blocks"]:
                            for line in block.get("lines",[]):
                                for span in line["spans"]:
                                    t=span["text"].strip()
                                    if t.startswith("PdP ") and len(t)==7 and t[4:].isdigit():
                                        tags.append(int(t[4:]))
                    self.assertEqual(tags,list(range(1,pdp_counts[subject][year]+1)))
                    if subject=="bahasa_arab":
                        arab_links+=sum(len(page.get_links()) for page in pdf)
                else:
                    self.assertEqual(order,sorted(order),
                                     "Subjek lain mesti kekal LTR")
        self.assertEqual(rtl_count,10)
        self.assertEqual(arab_links,298)

    def test_no_new_page_and_no_layout_leaking_outside_original_spaces(self):
        l=self.layout
        for box in ("logo_interior_top_left","logo_image_safe_top_left",
                    "school_row_top_left","teacher_row_top_left"):
            x0,y0,x1,y1=l[box]
            self.assertGreaterEqual(x0,0)
            self.assertGreaterEqual(y0,0)
            self.assertLessEqual(x1,l["page_width"])
            self.assertLessEqual(y1,l["page_height"])
            self.assertLess(x0,x1)
            self.assertLess(y0,y1)
        for f in ("school_row_top_left","teacher_row_top_left"):
            box=l[f]
            self.assertGreater(box[0],200)
            self.assertLess(box[2],l["identity_panel_top_left"][2])
            self.assertLess(box[3]-box[1],32)
        self.assertEqual(l["expected_underscore_lines_per_cover"],2)


if __name__=="__main__":
    unittest.main()
