"""Reproducible source-facsimile appendix for five user-supplied original Arabic DSKP PDFs.

Run locally with the real original KPM PDFs already downloaded from the user's
Drive. No silent OCR, no artificial Arabic full statements and no publishing.
Uses original PDF pages with exact SHA-256 provenance and 117 code/page links.
"""
from __future__ import annotations
from pathlib import Path
import hashlib
import json

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/bahasa_arab_rpt2027_y2_y6_117_sp_pdf_page_evidence_20261107.json"

def build_all(source_dir:Path, output_dir:Path):
    import fitz
    data=json.loads(LEDGER.read_text(encoding="utf-8"))
    if (data["status"]!="STAGING_117_CODE_AND_PDF_PAGE_VERIFIED_ONLY"
        or data["summary"]["full_arabic_statement_signoffs"]!=0):
        raise ValueError("Arabic DSKP ledger no longer source-only")
    plans=[]
    for year in range(2,7):
        row=data["year2"] if year==2 else next(x for x in data["years"] if x["year"]==year)
        entries=[(e["sp_code"],e["pdf_page"]) for e in row["entries"]]
        pages=row["pdf_pages"] if year==2 else row["pdf_page_count"]
        expected_sha=row["pdf_sha256"]
        if len(entries)!={2:19,3:23,4:25,5:25,6:25}[year]:
            raise ValueError("Arabic code-count changed")
        if len({code for code,_ in entries})!=len(entries) or any(
            type(p) is not int or p<1 or p>pages for _,p in entries
        ):
            raise ValueError("Arabic source-page evidence invalid")
        plans.append((year,entries,expected_sha,pages))
    if sum(len(x[1]) for x in plans)!=117:
        raise ValueError("Arabic 117 SP page anchors missing")
    target_dir=Path(output_dir);target_dir.mkdir(parents=True,exist_ok=True)
    output=[]
    for year,entries,sha,pages in plans:
        source=Path(source_dir)/f"DSKP KSSR (Semakan 2017) Bahasa Arab Tahun {year}.pdf"
        if not source.is_file() or hashlib.sha256(source.read_bytes()).hexdigest()!=sha:
            raise ValueError(f"Year {year}: original Arabic DSKP missing, changed or wrong edition")
        with fitz.open(source) as original:
            if original.page_count!=pages:
                raise ValueError(f"Year {year}: original Arabic PDF page count changed")
            unique=sorted({p for _,p in entries})
            doc=fitz.open()
            cover=doc.new_page(width=595,height=842)
            cover.insert_text((40,52),"CIKGULAJU | RPT 2027 | BAHASA ARAB",fontsize=16,fontname="hebo")
            cover.insert_text((40,80),f"TAHUN {year} - KOD SP KE HALAMAN DSKP ASAL",fontsize=12,fontname="hebo")
            cover.insert_text((40,108),"LAMPIRAN SEMAKAN DRAF - BUKAN PENGESAHAN AKADEMIK",fontsize=10,fontname="hebo",color=(0.7,0.2,0.1))
            cover.insert_text((40,135),"Pautan kod membuka halaman visual PDF asal, bukan transkripsi automatik.",fontsize=9)
            cover.insert_text((40,153),"Tidak bermakna setiap teks Arab/aktiviti PdP telah diluluskan.",fontsize=9)
            for number in unique:
                doc.insert_pdf(original,from_page=number-1,to_page=number-1)
            positions={p:i+1 for i,p in enumerate(unique)}
            doc.set_toc([[1,f"DSKP asal PDF hlm {p}",positions[p]+1] for p in unique])
            cover=doc[0]
            for i,(code,p) in enumerate(sorted(entries,key=lambda x:tuple(int(n) for n in x[0].split(".")))):
                x=42+(i//13)*258;y=195+(i%13)*40
                cover.insert_text((x,y),f"SP {code}",fontsize=12,fontname="hebo")
                cover.insert_text((x+5,y+14),f"DSKP asal PDF hlm {p}",fontsize=8)
                cover.insert_link({"kind":fitz.LINK_GOTO,"from":fitz.Rect(x-4,y-16,x+225,y+18),
                                   "page":positions[p],"to":fitz.Point(0,0)})
            path=target_dir/f"BAHASA_ARAB_TAHUN_{year}_2027_LAMPIRAN_DSKP_VISUAL_DRAF.pdf"
            doc.save(path,garbage=4,deflate=True)
            doc.close()
        with fitz.open(path) as check:
            if len(check[0].get_links())!=len(entries) or check.page_count!=len(unique)+1:
                raise ValueError(f"Year {year} appendix links/pages incomplete")
        output.append(path)
    return output

if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--source-dir",type=Path,required=True)
    p.add_argument("--output-dir",type=Path,required=True)
    a=p.parse_args()
    for path in build_all(a.source_dir,a.output_dir):
        print("Arabic visual source appendix DRAF:",path)
