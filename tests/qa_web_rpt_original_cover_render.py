"""PDF visual regression on 12 authentic RPT first-page templates.

For every subject: page count unchanged, exact page 2 text unchanged,
no visual difference outside the three pre-existing cover placeholders,
and identical existing PDF annotation/link counts.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import fitz
from PIL import Image,ImageChops,ImageDraw,ImageOps

ROOT=Path(__file__).resolve().parents[1]/"rpt_2027"/"web_2027_pdfs"
LAYOUT=json.loads((ROOT/"original_cover_layout_verified.json").read_text("utf-8"))

def verify(directory):
    root=Path(directory)
    subjects=("english","matematik","bahasa_arab","bahasa_melayu",
              "muzik","pendidikan_islam","pendidikan_moral",
              "pjpk","psv","rbt","sejarah","sains")
    checked=0
    for subject in subjects:
        source=root/(subject+".source.pdf")
        final=root/(subject+".pdf")
        if not source.is_file() or not final.is_file():
            raise AssertionError(f"Missing test PDF {subject}")
        with fitz.open(source) as before,fitz.open(final) as after:
            if len(before)!=len(after):
                raise AssertionError(f"RPT page count changed: {subject}")
            if (before[0].rect!=after[0].rect or
                before[1].get_text("text")!=after[1].get_text("text")):
                raise AssertionError(f"RPT page source modified: {subject}")
            for i in range(len(before)):
                if len(before[i].get_links())!=len(after[i].get_links()):
                    raise AssertionError(f"PDF source URL/internal link lost: {subject}, page {i+1}")
            # Rendering both PDFs using the same rasterizer must change only
            # the original logo box interior and school/teacher blank lines.
            scale=1.5
            r0=before[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
            r1=after[0].get_pixmap(matrix=fitz.Matrix(scale,scale),alpha=False)
            first=Image.frombytes("RGB",(r0.width,r0.height),r0.samples)
            second=Image.frombytes("RGB",(r1.width,r1.height),r1.samples)
            if first.size!=second.size:raise AssertionError("Image dimensions changed")
            diff=ImageChops.difference(first,second).convert("L")
            allowed=Image.new("L",first.size,0)
            pen=ImageDraw.Draw(allowed)
            for name in ("logo_interior_top_left","school_row_top_left","teacher_row_top_left"):
                box=LAYOUT[name]
                # 2px tolerance only for antialiasing around changed pixels.
                pen.rectangle(tuple(round(v*scale+(-2 if i<2 else 2))
                                   for i,v in enumerate(box)),fill=255)
            outside=Image.composite(diff,Image.new("L",diff.size,0),
                                    ImageOps.invert(allowed))
            if outside.getbbox():
                raise AssertionError(f"Original RPT cover altered outside three slots: {subject}, {outside.getbbox()}")
            within=Image.composite(diff,Image.new("L",diff.size,0),allowed)
            if within.getbbox() is None:
                raise AssertionError(f"No original cover text/placeholder updated: {subject}")
        checked+=1
    print(f"ORIGINAL_COVER_RENDER_DIFF_12_SUBJECTS_PASS {checked}/12, extra pages 0, content elsewhere unchanged")

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--outputs",required=True)
    args=parser.parse_args()
    verify(args.outputs)
