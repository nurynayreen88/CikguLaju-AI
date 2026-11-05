#!/usr/bin/env python3
"""Offline Sejarah RPH/RPT 2027 PDF smoke: staging only, no production imports.
Do not infer material approval from PDF layout or structural success.
"""
from __future__ import annotations
from pathlib import Path
from html import escape
import json
import re
from weasyprint import HTML
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"output"/"sejarah_pdf_preview_qa"
EXPECTED=(4,5,6)
BREAKS={
    "A":[("2027-03-05","2027-03-13"),("2027-05-21","2027-06-05"),("2027-08-27","2027-09-04")],
    "B":[("2027-03-06","2027-03-14"),("2027-05-22","2027-06-06"),("2027-08-28","2027-09-05")]
}
def check_calendar(data,year):
    from datetime import date
    for x in data["lessons"]:
        for group in ("A","B"):
            start=date.fromisoformat(x["weeks"][group]["start"])
            end=date.fromisoformat(x["weeks"][group]["end"])
            assert date(2027,1,4)<=start<=end<=date(2027,12,3),(year,x["id"],group,start,end)
            for a,b in BREAKS[group]:
                assert end<date.fromisoformat(a) or start>date.fromisoformat(b),("PdP in KPM term break",year,x["id"],group,a,b)

def pdf_text(reader):
    return "\n".join((page.extract_text(extraction_mode="plain") or "") for page in reader.pages)

def run():
    OUT.mkdir(parents=True,exist_ok=True)
    manifest=[]
    for year in EXPECTED:
        data=json.loads((ROOT/f"rph_standalone/sejarah/y{year}_2027_rph_DRAF.json").read_text(encoding="utf-8"))
        check_calendar(data,year)
        for kind in ("RPH","RPT"):
            if kind=="RPH":
                src=ROOT/f"rph_standalone/sejarah/RPH_SEJARAH_TAHUN_{year}_2027_DRAF.html"
            else:
                src=ROOT/f"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.html"
            output=OUT/f"{kind}_SEJARAH_TAHUN_{year}_2027_DRAF_PREVIEW.pdf"
            raw=src.read_text(encoding="utf-8")
            assert "DRAF" in raw and "CIKGULAJU" in raw
            # Temporary output is only uploaded as a CI preview artifact. Never release automatically.
            HTML(string=raw,base_url=str(src.parent)).write_pdf(str(output))
            pdf=PdfReader(str(output),strict=True)
            count=len(pdf.pages)
            expect_landscape=kind=="RPT"
            assert count>=3 and all((float(p.mediabox.width)>float(p.mediabox.height))==expect_landscape for p in pdf.pages), (year,kind,"orientation")
            txt=pdf_text(pdf)
            # HTML already includes a cover before the two RPT group sections.
            if kind=="RPH":
                assert count==36,("ONE_A4_RPH_PAGE_PER_PDP_FAILED",year,count)
                assert all(re.search(rf"PdP\s+{n}(?!\d)",txt) for n in range(1,37)),("MISSING_RPH_NUMBER",year)
                assert "PBD" in txt and "SEJARAH" in txt
            else:
                assert "Kumpulan A" in txt and "Kumpulan B" in txt,(year,"missing groups")
                assert re.search(r"RANCANGAN\s+PENGAJARAN\s+TAHUNAN",txt),(year,"missing cover")
                for n in range(1,37):
                    assert len(re.findall(rf"(?<!\d){n}(?!\d)",txt))>=2,(year,"missing RPT row",n)
            manifest.append({"year":year,"document":kind,"pages":count,"bytes":output.stat().st_size,"orientation":"landscape" if expect_landscape else "portrait","preview":True,"ready":False})
            print(f"{kind} Y{year}: {count} pages, {output.stat().st_size} bytes, PDF searchable, {'landscape' if expect_landscape else 'portrait'}",flush=True)
    (OUT/"manifest.json").write_text(json.dumps({"status":"DRAF_PDF_PREVIEW_ONLY","records":manifest},indent=2)+"\n",encoding="utf-8")
    assert len(manifest)==6
if __name__=="__main__":
    run()
