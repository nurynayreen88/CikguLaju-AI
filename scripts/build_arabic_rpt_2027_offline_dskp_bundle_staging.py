"""Repackage 5 Arabic 2027 RPT DRAFT PDFs with offline, visual KPM DSKP annexes.

The original year-specific official DSKP pages are appended to each RPT as
facsimiles; the 298 SOURCE links become internal PDF jumps. This never
transcribes Arabic or marks the SK/SP academic content as verified.
Requires already supplied/read-only annex PDFs; never downloads from Drive
or writes back to DB, GitHub source CSV, Telegram or production.
"""
from __future__ import annotations

import argparse
import json
import re
import zipfile
from pathlib import Path

import fitz

YEARS={2:60,3:60,4:58,5:60,6:60}
RPT_TEMPLATE="CIKGULAJU_RPT_BAHASA_ARAB_TAHUN_{year}_2027_LIMA_LAJUR_DRAF.pdf"
ANNEX_TEMPLATE="BAHASA_ARAB_TAHUN_{year}_2027_DSKP_117_SP_RUJUKAN_VISUAL_STAGING.pdf"
OUTPUT_TEMPLATE="CIKGULAJU_RPT_BAHASA_ARAB_TAHUN_{year}_2027_DSKP_ASAL_OFFLINE_DRAF.pdf"
OUTPUT_STATUS="STAGING_ARABIC_5_RPT_OFFLINE_FACSIMILE_NOT_ACADEMIC_SIGNOFF"

def repack_year(rpt_bytes, annex_pdf, year, records, source_uri, destination):
    if year not in YEARS or len(records)!={2:19,3:23,4:25,5:25,6:25}[year]:
        raise ValueError("Arabic year/source-code coverage invalid")
    if any(r.get("year")!=year or r.get("full_statement_text_verified") is not False
           or r.get("source_visual_facsimile") is not True for r in records):
        raise ValueError("Arabic code-page reference unexpectedly approved/missing")
    if not re.fullmatch(r"https://drive\.google\.com/file/d/[A-Za-z0-9_-]{20,}/view",
                        source_uri):
        raise ValueError("DSKP source PDF URI must be original Google Drive PDF")
    source_pages=sorted({r["pdf_page"] for r in records})
    if any(type(p) is not int or not 1<=p<=200 for p in source_pages):
        raise ValueError("Original DSKP PDF pages invalid")
    mapping={page:i+1 for i,page in enumerate(source_pages)}
    doc=fitz.open(stream=rpt_bytes,filetype="pdf")
    annex=fitz.open(annex_pdf)
    try:
        if (len(annex)!=len(source_pages)+1 or
            f"TAHUN {year}" not in annex[0].get_text().upper()):
            raise ValueError("Wrong original DSKP visual annex or page mapping")
        for p in annex:
            if p.rect.width<=0 or p.rect.height<=0:
                raise ValueError("Original DSKP visual page malformed")
        for page in list(annex)[1:]:
            heading=" ".join(page.get_text()[:200].upper().split())
            if f"BAHASA ARAB TAHUN {year}" not in heading:
                raise ValueError("Source facsimile belongs to wrong DSKP year")
        original_pages=len(doc)
        if original_pages<2:
            raise ValueError("RPT body PDF missing")
        if "DRAF" not in doc[0].get_text().upper():
            # Explicit DRAF label may be in the PDF metadata/title, not cover.
            if "DRAF" not in (doc.metadata.get("title") or "").upper():
                raise ValueError("Only unapproved RPT source may be re-packaged")
        doc.insert_pdf(annex,links=True)
        jumps=0
        # PyMuPDF mutates the shared PDF link objects when deleting and
        # inserting annotations. Process pages in reverse to preserve links
        # that have not yet been converted (tested against 60-link PDFs).
        for i in reversed(range(original_pages)):
            p=doc[i]
            for link in reversed(list(p.get_links())):
                if link.get("kind")!=fitz.LINK_URI:
                    continue
                if link.get("uri")!=source_uri:
                    raise ValueError("Unrecognized external link in Arabic RPT")
                text=p.get_textbox(link["from"])
                m=re.search(r"halaman PDF\s+(\d+)",text)
                if not m:
                    raise ValueError("Source page label not present in clickable link")
                source_page=int(m.group(1))
                if source_page not in mapping:
                    raise ValueError("Linked DSKP source page absent from annex")
                rect=fitz.Rect(link["from"])
                p.delete_link(link)
                p.insert_link({"kind":fitz.LINK_GOTO,"from":rect,
                               "page":original_pages+mapping[source_page],
                               "to":fitz.Point(0,35)})
                jumps+=1
        if jumps!=YEARS[year]:
            raise ValueError(f"Expected {YEARS[year]} distinct PdP-source links, got {jumps}")
        out=Path(destination)
        if "DRAF" not in out.stem.upper() or out.suffix.lower()!=".pdf":
            raise ValueError("Output must remain an independently named DRAF PDF")
        out.parent.mkdir(parents=True,exist_ok=True)
        doc.save(out,garbage=4,deflate=True)
    finally:
        doc.close()
        annex.close()
    with fitz.open(out) as check:
        internal=[x for p in list(check)[:original_pages]
                  for x in p.get_links() if x.get("kind")==fitz.LINK_GOTO]
        external=[x for p in list(check)[:original_pages]
                  for x in p.get_links() if x.get("kind")==fitz.LINK_URI]
        if (len(internal)!=YEARS[year] or external
            or any(not original_pages+1<=x["page"]<len(check) for x in internal)):
            raise ValueError("Original Arabic DSKP internal links do not pass QA")
        if not all(p.rect.width>p.rect.height for p in list(check)[:original_pages]):
            raise ValueError("Original 2026-format RPT landscape body altered")
        return {"year":year,"rpt_pages":original_pages,
                "appended_source_pages":len(check)-original_pages,
                "link_count":len(internal),"total_pages":len(check),
                "source_text_academic_signoffs":0,
                "release_ready":False}

def package(rpt_zip,annex_dir,source_index,source_ledger,out_zip):
    idx=json.loads(Path(source_index).read_text("utf-8"))
    if idx.get("status")!="STAGING_SOURCE_VISUAL_ONLY_NOT_FULL_TEXT_SIGNOFF" or idx.get("release_ready") is not False or len(idx.get("records",[]))!=117:
        raise ValueError("Wrong 117-SP visual facsimile evidence index")
    ledger=json.loads(Path(source_ledger).read_text("utf-8"))
    if (ledger.get("status")!="STAGING_117_CODE_AND_PDF_PAGE_VERIFIED_ONLY"
        or ledger["summary"]["full_arabic_statement_signoffs"]!=0):
        raise ValueError("Source page ledger unexpectedly approved")
    sources={2:ledger["year2"],**{r["year"]:r for r in ledger["years"]}}
    target=Path(out_zip)
    if "STAGING" not in target.stem.upper() or target.suffix.lower()!=".zip":
        raise ValueError("Archive must carry explicit STAGING label")
    produced=[]
    with zipfile.ZipFile(rpt_zip) as archived,zipfile.ZipFile(target,"w",zipfile.ZIP_DEFLATED) as output:
        for year in YEARS:
            rows=[x for x in idx["records"] if x.get("year")==year]
            source=sources[year]
            if (len(rows)!=len(source["entries"])
                or {r["sp_code"]:r["pdf_page"] for r in rows}!=
                   {e["sp_code"]:e["pdf_page"] for e in source["entries"]}
                or any(r["source_sha256"]!=source["pdf_sha256"] for r in rows)):
                raise ValueError(f"Year {year} PDF source anchors/checksums inconsistent")
            fn=RPT_TEMPLATE.format(year=year)
            annex=Path(annex_dir)/ANNEX_TEMPLATE.format(year=year)
            dest=target.parent/OUTPUT_TEMPLATE.format(year=year)
            info=repack_year(archived.read(fn),annex,year,rows,
                             source["source_url"],dest)
            produced.append(info)
            output.write(dest,dest.name)
        if len(produced)!=5 or sum(x["link_count"] for x in produced)!=298:
            raise ValueError("5 Arabic years and 298 complete source links required")
        output.writestr("MANIFEST_DRAF.json",json.dumps({
            "status":OUTPUT_STATUS,"years":produced,
            "all_298_source_links_internal":True,
            "approved_full_arabic_sp_transcriptions":0,
            "ready_for_web_telegram":False,"production_writes":0
        },ensure_ascii=False,indent=2)+"\n")
        output.writestr("BACA_DULU.txt",
                        "Lima PDF RPT Bahasa Arab Tahun 2-6 DRAF 2027.\n"
                        "Klik Buka DSKP asal pada mana-mana PdP untuk terus melihat halaman DSKP asal "
                        "yang dimasukkan di penghujung PDF berkenaan. Tidak perlu akses Drive.\n"
                        "Lampiran ini ialah BUKTI VISUAL, bukan kelulusan teks penuh SK/SP, jadual, atau Web/Telegram.\n")
    return target,produced

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--rpt-zip",type=Path,required=True)
    parser.add_argument("--annex-dir",type=Path,required=True)
    parser.add_argument("--source-index",type=Path,required=True)
    parser.add_argument("--source-ledger",type=Path,required=True)
    parser.add_argument("--out-zip",type=Path,required=True)
    a=parser.parse_args()
    path,summary=package(a.rpt_zip,a.annex_dir,a.source_index,
                         a.source_ledger,a.out_zip)
    print("ARABIC_RPT_OFFLINE_DRAF",path,
          sum(x["link_count"] for x in summary),"source links")
