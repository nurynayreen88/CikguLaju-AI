"""Safely install exactly 10 RPT2027 RTL PDFs from verified source-CI artifact.

Change only BAHASA_ARAB and PENDIDIKAN_ISLAM Year2-6.
Keep the original cover, paid gate, private profile placeholders, draft labels,
untouched 46 RPT PDFs, and native source PDF links. Run in an isolated
GitHub Actions feature branch. No user database, Telegram, billing or quota.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
import json
import re
from pathlib import Path
import fitz

YEARS=range(2,7)
SUBJECTS=("pendidikan_islam","bahasa_arab")
EXPECTED={f"{sub}:{year}" for sub in SUBJECTS for year in YEARS}
SOURCE_NAME=re.compile(
    r"^CIKGULAJU_RPT_(PENDIDIKAN_ISLAM|BAHASA_ARAB)_TAHUN_([2-6])_2027_LIMA_LAJUR_DRAF\.pdf$")
LABELS=("MINGGU / TARIKH","UNIT / TAJUK / PDP","SK","SP","CATATAN / BAHAN")
CODE_COUNTS={
    "bahasa_arab":{2:60,3:60,4:58,5:60,6:60},
    "pendidikan_islam":{2:112,3:147,4:151,5:143,6:143}
}

def source_files(directory):
    result={}
    for file in Path(directory).rglob("*.pdf"):
        matched=SOURCE_NAME.fullmatch(file.name)
        if not matched:
            continue
        subject=matched.group(1).lower()
        year=int(matched.group(2))
        key=f"{subject}:{year}"
        if key in result:
            raise ValueError("Duplicate RTL RPT source: "+key)
        result[key]=file
    if set(result)!=EXPECTED or len(result)!=10:
        raise ValueError("Expected ten explicitly named Islamic and Arabic RPT PDFs")
    return result

def validate_pdf(file, subject, year, old_pdf, cover_layout):
    raw=file.read_bytes()
    if not 8_000<=len(raw)<=25*1024*1024 or not raw.startswith(b"%PDF-"):
        raise ValueError("Missing or malformed PDF")
    with fitz.open(file) as pdf,fitz.open(old_pdf) as old:
        if not 2<=pdf.page_count<=300:
            raise ValueError("Invalid page count")
        if pdf[0].rect!=old[0].rect:
            raise ValueError("Cover dimensions changed")
        if pdf[0].get_text("text")!=old[0].get_text("text"):
            raise ValueError("Original cover text changed")
        if pdf[0].get_pixmap(alpha=False).samples!=old[0].get_pixmap(alpha=False).samples:
            raise ValueError("Original cover pixels changed")
        # Important: the first-page teacher profile cover stamp is anchored
        # by a separate geometry audit; its spans must remain unchanged.
        first=pdf[0]
        for label in ("LOGO SEKOLAH","NAMA SEKOLAH","NAMA GURU"):
            if not first.search_for(label):
                raise ValueError("Original teacher profile placeholder lost")
        if abs(first.rect.width-cover_layout["page_width"])>cover_layout["tolerance_pt"]:
            raise ValueError("Cover layout diverged from locked template")
        codes=CODE_COUNTS[subject][year]
        # PyMuPDF page.get_text() may join a Jawi SP cell directly into
        # "PdP 001" from a neighboring cell on the same baseline, removing
        # the Unicode word boundary. Count EXACT PDF text spans instead.
        found=[]
        for page in list(pdf)[1:]:
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for span in line["spans"]:
                        tag=span["text"].strip()
                        if re.fullmatch(r"PdP \d{3}",tag):
                            found.append(int(tag[-3:]))
        if found!=list(range(1,codes+1)):
            raise ValueError(f"PdP sequence missing, repeated or out of order in {subject} {year}: "
                             f"found {len(found)}, expected {codes}")
        # Header width follows the original columns, but physical order is
        # mirrored: far-right Minggu > Unit > SK > SP > far-left Catatan.
        for page in list(pdf)[1:]:
            heads={}
            for block in page.get_text("dict")["blocks"]:
                for line in block.get("lines",[]):
                    for span in line["spans"]:
                        label=span["text"].strip()
                        if label in LABELS and 40<span["bbox"][1]<95:
                            heads[label]=span["bbox"][0]
            if set(heads)!=set(LABELS):
                raise ValueError("RPT exact column-header spans missing")
            if not (heads["CATATAN / BAHAN"]<heads["SP"]<
                    heads["SK"]<heads["UNIT / TAJUK / PDP"]<
                    heads["MINGGU / TARIKH"]):
                raise ValueError("RPT is not physically RTL")
            if heads["MINGGU / TARIKH"]<650:
                raise ValueError("Week/date column not at far-right")
            if page.rect.width<=page.rect.height:
                raise ValueError("RPT page must remain landscape")
        # No 2027 SK/SP code rows, PdP, DSKP hyperlinks may be erased by
        # reflow. For Arabic use source-row count and preserved source links.
        old_links=sum(len(page.get_links()) for page in old)
        new_links=sum(len(page.get_links()) for page in pdf)
        if subject=="bahasa_arab":
            if old_links!=new_links or new_links<codes:
                raise ValueError("Arabic DSKP source PDF links lost")
        elif old_links!=new_links:
            raise ValueError("Unexpected PI PDF links change")
        return {"sha256":sha256(raw).hexdigest(),"bytes":len(raw),
                "pages":pdf.page_count,"status":"DRAF",
                "source_pdp":codes,"original_links":old_links,
                "updated_links":new_links}

def install(source_dir,web_assets):
    original=Path(web_assets)
    mpath=original/"manifest.json"
    lpath=original/"original_cover_layout_verified.json"
    manifest=json.loads(mpath.read_text("utf-8"))
    layout=json.loads(lpath.read_text("utf-8"))
    if (manifest.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
        or manifest.get("count")!=56
        or len(manifest.get("files",{}))!=56
        or layout.get("status")!="ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256"
        or set(manifest["files"])!=set(layout.get("source_sha256_by_subject_year",{}))):
        raise ValueError("Web RPT source manifest/cover hash ledger not trusted")
    sources=source_files(source_dir)
    previous_sha={key:manifest["files"][key]["sha256"] for key in EXPECTED}
    updates={}
    for key,source in sorted(sources.items()):
        subject,year_s=key.split(":")
        year=int(year_s)
        entry=manifest["files"][key]
        dest=original/entry["path"]
        if dest.is_symlink() or not dest.is_file():
            raise ValueError("Unsafe existing PDF source: "+key)
        old=dest.read_bytes()
        if sha256(old).hexdigest()!=entry["sha256"]:
            raise ValueError("Web original source PDF SHA mismatch: "+key)
        revised=validate_pdf(source,subject,year,dest,layout)
        if old==source.read_bytes():
            # Rerun is safe: no data alteration or duplicate rewriting.
            updates[key]=revised
            continue
        updates[key]=revised
    if set(updates)!=EXPECTED:
        raise ValueError("RTL patch inventory unexpected")
    untouched={key:entry.copy() for key,entry in manifest["files"].items() if key not in EXPECTED}
    for key in EXPECTED:
        subject,year_s=key.split(":")
        dest=original/manifest["files"][key]["path"]
        dest.write_bytes(sources[key].read_bytes())
        manifest["files"][key].update({
            field:updates[key][field] for field in ("sha256","bytes","pages")
        })
        layout["source_sha256_by_subject_year"][key]=updates[key]["sha256"]
    manifest["pages"]=sum(e["pages"] for e in manifest["files"].values())
    manifest["rtl_pendidikan_islam_bahasa_arab_20261108"]={
        "subject_year_count":10,"status":"DRAF","note":
        "Same RPT content; physically mirrored five columns for Jawi/Arabic. Original cover unchanged.",
    }
    layout["rtl_pi_arabic_pdf_hashes_updated_without_cover_geometry_changes"]=True
    if any(manifest["files"][key]!=value for key,value in untouched.items()):
        raise ValueError("Unexpected change in the other 46 PDFs")
    mpath.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n","utf-8")
    lpath.write_text(json.dumps(layout,indent=2,ensure_ascii=False)+"\n","utf-8")
    # Critical: recheck all 56 hashes and no staged academic approval.
    for key,entry in manifest["files"].items():
        pdf=original/entry["path"]
        data=pdf.read_bytes()
        if len(data)!=entry["bytes"] or sha256(data).hexdigest()!=entry["sha256"]:
            raise ValueError("56-catalog after-update SHA mismatch: "+key)
    assert manifest["status"]=="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
    audit={
        "status":"DRAF_RTL_LAYOUT_ONLY_NOT_ACADEMIC_FINAL",
        "year":2027,
        "changed_subjects":list(SUBJECTS),
        "changed_years":list(YEARS),
        "rtl_updated_count":len(updates),
        "web_catalog_pdf_count":len(manifest["files"]),
        "remaining_other_subject_pdfs_sha_unchanged":46,
        "original_cover_geometry_unchanged":True,
        "source_links_checked":True,
        "production_db_modified":False,
        "telegram_modified":False,
        "source_rpt_content_not_academically_reapproved":True,
        "entries":{key:{"before_sha256":previous_sha[key],
                         "after_sha256":updates[key]["sha256"],
                         "source_pdp":updates[key]["source_pdp"],
                         "pages":updates[key]["pages"],
                         "links":updates[key]["updated_links"]}
                  for key in sorted(updates)}
    }
    (original/"RTL_PI_ARABIC_20261108_DRAF_AUDIT.json").write_text(
        json.dumps(audit,indent=2,ensure_ascii=False)+"\n","utf-8")
    print("RTL_PI_ARABIC_10_PDF_56_ASSET_MANIFEST_PRESERVED",json.dumps({
        "updates":updates,"pdf_pages":manifest["pages"],"unchanged_pdfs":46
    },ensure_ascii=False))
    return updates

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",required=True)
    parser.add_argument("--assets",default="rpt_2027/web_2027_pdfs")
    args=parser.parse_args()
    install(args.sources,args.assets)
