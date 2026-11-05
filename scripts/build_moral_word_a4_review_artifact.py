#!/usr/bin/env python3
"""Build the five Moral supplementary Word packs for physical A4 print QA.

The script only exports already-versioned source. It does not touch live data.
Actual 54-page pagination must be independently verified after Word/PDF render.
"""
from __future__ import annotations
import argparse
from pathlib import Path

from docx import Document
from docx.shared import Cm
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from rpt_2027.pendidikan_moral.complete_96_downloads import build_rph_docx

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--outdir",required=True)
    d=Path(p.parse_args().outdir)
    d.mkdir(parents=True,exist_ok=True)
    for year in range(2,7):
        path=build_rph_docx(year,d/f"Moral_Tahun{year}_Pengukuhan_54_RPH.docx")
        doc=Document(path)
        sec=doc.sections[0]
        # Page dimensions are A4 portrait; paragraph break alone doesn't
        # guarantee one RPH per physical page after Word render.
        assert abs(sec.page_width.cm-21.0)<0.03
        assert abs(sec.page_height.cm-29.7)<0.03
        heads=[x.text for x in doc.paragraphs if x.text.startswith("RPH PENDIDIKAN MORAL TAHUN")]
        assert len(heads)==54,(year,len(heads))
        print("EXPORTED A4 Word pack",year,"54 RPH",path.stat().st_size,"bytes")
    print("OUTPUT NOT YET VERIFIED AS 54 PHYSICAL PAGES; check with LibreOffice/PDF renderer.")
if __name__=="__main__":
    main()
