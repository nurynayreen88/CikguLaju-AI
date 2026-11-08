"""Stage/validate exactly 15 subject-native-header RPT2027 PDFs for Web.

Do not modify source curriculum, user DB, Telegram, billing, trial credits,
RPT original cover page, or the 41 RPT PDFs belonging to other subjects.

PI uses five Jawi headings, Arabic uses Arabic, and English uses English.
Content rows, PDF links, source PdP IDs, week merge and physical RTL/LTR
are the original source reflow; changes are only the five headings.
"""
from __future__ import annotations

import argparse
from hashlib import sha256
from pathlib import Path
import json
import re
import fitz

SUBJECTS=("pendidikan_islam","bahasa_arab","english")
YEARS=range(2,7)
UPDATE_KEYS={f"{subject}:{year}" for subject in SUBJECTS for year in YEARS}
EXPECTED={
    "pendidikan_islam":{2:112,3:147,4:151,5:143,6:143},
    "bahasa_arab":{2:60,3:60,4:58,5:60,6:60},
    "english":{2:160,3:160,4:160,5:160,6:160},
}
PATTERN=re.compile(r"^CIKGULAJU_RPT_(PENDIDIKAN_ISLAM|BAHASA_ARAB|ENGLISH)_TAHUN_([2-6])_2027_LIMA_LAJUR_DRAF\.pdf$")
ENGLISH_LABELS=("WEEK / DATE","UNIT / TOPIC / LESSON","CONTENT STANDARD",
                "LEARNING STANDARD","NOTES / MATERIALS")
MALAY_LABELS=("MINGGU / TARIKH","UNIT / TAJUK / PDP","CATATAN / BAHAN")
# Coordinates anchored to unchanged reportlab landscape five-column layout.
RTL_BANDS=(29,193,403,528,708,813)

def native(char):
    return "\u0600" <= char <= "\u08ff" or "\ufb50" <= char <= "\ufeff"

def pdf_header_spans(page):
    return [s for block in page.get_text("dict")["blocks"]
            for line in block.get("lines",[])
            for s in line["spans"]
            if 46 <= s["bbox"][1] < 83 and s["bbox"][3] < 90
            and s["text"].strip()]

def source_map(source_dir):
    found={}
    for pdf in Path(source_dir).rglob("*.pdf"):
        match=PATTERN.fullmatch(pdf.name)
        if not match:
            continue
        subject=match.group(1).lower()
        year=int(match.group(2))
        key=f"{subject}:{year}"
        if key in found:
            raise ValueError("Duplicate source PDF: "+key)
        found[key]=pdf
    if set(found)!=UPDATE_KEYS:
        raise ValueError("Expected exactly fifteen subject/year PDF sources")
    return found

def pdp_ids(pdf,subject):
    prefix="Lesson " if subject=="english" else "PdP "
    result=[]
    for page in list(pdf)[1:]:
        for block in page.get_text("dict")["blocks"]:
            for line in block.get("lines",[]):
                for span in line["spans"]:
                    label=span["text"].strip()
                    if re.fullmatch(re.escape(prefix)+r"\d{3}",label):
                        result.append(int(label[-3:]))
    return result

def validate_new_pdf(source,old,entry,subject,year):
    raw=Path(source).read_bytes()
    if (not raw.startswith(b"%PDF-") or
        len(raw)<8000 or len(raw)>25*1024*1024):
        raise ValueError("Malformed PDF "+str(source))
    with fitz.open(stream=raw,filetype="pdf") as pdf,fitz.open(old) as baseline:
        if not (2<=len(pdf)<=300) or pdf[0].rect!=baseline[0].rect:
            raise ValueError("PDF page shape/cover changed")
        # The user's original cover layout, with 3 editable teacher fields,
        # must remain PIXEL IDENTICAL; no extra cover, no new page at front.
        if pdf[0].get_text("text")!=baseline[0].get_text("text"):
            raise ValueError("User's original cover text changed")
        if pdf[0].get_pixmap(alpha=False).samples!=baseline[0].get_pixmap(alpha=False).samples:
            raise ValueError("User's original cover pixels changed")
        actual_pdp=pdp_ids(pdf,subject)
        expected=list(range(1,EXPECTED[subject][year]+1))
        if actual_pdp!=expected:
            raise ValueError(f"{subject} Year{year} PdP/Lesson sequence changed: {len(actual_pdp)}")
        links_before=sum(len(page.get_links()) for page in baseline)
        links_after=sum(len(page.get_links()) for page in pdf)
        if links_after!=links_before or (subject=="bahasa_arab" and links_after!=EXPECTED[subject][year]):
            raise ValueError(f"{subject} Year{year} DSKP PDF source links changed")
        page=pdf[1]
        spans=pdf_header_spans(page)
        words=" ".join(s["text"] for s in spans)
        if any(label in words for label in MALAY_LABELS):
            raise ValueError(f"Malay table heading remains for {subject} {year}")
        if subject=="english":
            # English text may wrap into two lines if a column is narrow.
            header=" ".join(words.split())
            if not all(label in header for label in ENGLISH_LABELS):
                raise ValueError(f"English table headings untranslated: {header[:350]}")
            if any(native(ch) for ch in header):
                raise ValueError("English title unexpectedly contains Arabic script")
            for pg in list(pdf)[1:]:
                if any(label in pg.get_text("text") for label in MALAY_LABELS):
                    raise ValueError("Old Malay heading appears in English PDF")
        else:
            # 5 Arabic-script headers must occupy the 5 RTL physical bands,
            # even when a long header wraps into a second line.
            for a,b in zip(RTL_BANDS,RTL_BANDS[1:]):
                group=[sp for sp in spans if a<=sp["bbox"][0]<b]
                if not group or not any(native(ch) for sp in group for ch in sp["text"]):
                    raise ValueError(f"{subject} Year{year} header band {a}-{b} is not Jawi/Arabic")
            for pg in list(pdf)[1:]:
                if any(label in pg.get_text("text") for label in MALAY_LABELS):
                    raise ValueError("Old Malay heading appears in Jawi/Arabic PDF")
        if any(pg.rect.width<=pg.rect.height for pg in pdf):
            raise ValueError("Landscape PDF orientation lost")
        return {
            "sha256":sha256(raw).hexdigest(),
            "bytes":len(raw),
            "pages":len(pdf),
            "source_links":links_after,
            "lesson_count":len(actual_pdp),
        }

def install(source_dir,assets_dir,*,run_english,run_arabpi):
    base=Path(assets_dir)
    manifest_path=base/"manifest.json"
    layout_path=base/"original_cover_layout_verified.json"
    audit_path=base/"HEADINGS_PI_ARAB_EN_20261108_DRAF_AUDIT.json"
    manifest=json.loads(manifest_path.read_text("utf-8"))
    layout=json.loads(layout_path.read_text("utf-8"))
    if (manifest.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
        or manifest.get("count")!=56 or len(manifest.get("files",{}))!=56
        or set(manifest["files"])!=set(layout["source_sha256_by_subject_year"])
        or layout.get("status")!="ORIGINAL_COVER_TEMPLATE_LOCKED_TO_56_SOURCE_PDF_SHA256"):
        raise ValueError("56-web-RPT baseline manifest/cover audit not verified")
    sources=source_map(source_dir)
    if audit_path.is_file():
        previous=json.loads(audit_path.read_text("utf-8"))
        if (set(previous.get("entries",{}))==UPDATE_KEYS and
            all((base/manifest["files"][key]["path"]).read_bytes()==source.read_bytes()
                for key,source in sources.items())):
            if not all(sha256((base/entry["path"]).read_bytes()).hexdigest()==entry["sha256"]
                       for entry in manifest["files"].values()):
                raise ValueError("Existing 56-PDF manifest damaged")
            print("NATIVE_HEADINGS_15_PDFS_ALREADY_INSTALLED_IDENTICALLY")
            return previous

    # Validate all 56 originals BEFORE touching the working directory.
    for key,entry in manifest["files"].items():
        current=(base/entry["path"]).read_bytes()
        if (len(current)!=entry["bytes"] or
            sha256(current).hexdigest()!=entry["sha256"] or
            layout["source_sha256_by_subject_year"][key]!=entry["sha256"]):
            raise ValueError("Original SHA mismatch "+key)

    edits={}
    old_shas={key:manifest["files"][key]["sha256"] for key in UPDATE_KEYS}
    untouched={key:entry.copy() for key,entry in manifest["files"].items()
               if key not in UPDATE_KEYS}
    for key,src in sorted(sources.items()):
        subject,year_s=key.split(":")
        year=int(year_s)
        baseline=base/manifest["files"][key]["path"]
        edits[key]=validate_new_pdf(src,baseline,manifest["files"][key],subject,year)

    for key,src in sorted(sources.items()):
        manifest["files"][key].update(
            {k:edits[key][k] for k in ("sha256","bytes","pages")})
        manifest["files"][key]["source_run_id"]=(
            run_english if key.startswith("english:") else run_arabpi)
        layout["source_sha256_by_subject_year"][key]=edits[key]["sha256"]
        (base/manifest["files"][key]["path"]).write_bytes(src.read_bytes())

    if any(manifest["files"][key]!=value for key,value in untouched.items()):
        raise ValueError("Unexpected edit to other 41 RPT PDFs")
    manifest["pages"]=sum(e["pages"] for e in manifest["files"].values())
    manifest["native_table_headings_pi_arab_english_20261108"]={
        "count":15,"status":"DRAF","languages":{
            "pendidikan_islam":"Jawi","bahasa_arab":"Arabic","english":"English"},
        "other_pdf_files_unchanged":41,
        "original_cover_preserved":True,
    }
    audit={
        "status":"DRAF_LOCALIZED_TABLE_HEADERS_ONLY_NOT_ACADEMIC_FINAL",
        "year":2027,"subjects":list(SUBJECTS),"pdfs_updated":15,
        "other_pdfs_unchanged":41,
        "no_cover_changes":True,"no_db_writes":True,
        "no_telegram_writes":True,"no_billing_changes":True,
        "total_lessons_pdp":sum(x["lesson_count"] for x in edits.values()),
        "total_source_links":sum(x["source_links"] for x in edits.values()),
        "entries":{key:{
            "source_old_sha256":old_shas[key],
            "new_sha256":info["sha256"],
            "lesson_count":info["lesson_count"],
            "source_links":info["source_links"],
            "pages":info["pages"],
        }for key,info in sorted(edits.items())},
    }
    manifest_path.write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n","utf-8")
    layout_path.write_text(json.dumps(layout,indent=2,ensure_ascii=False)+"\n","utf-8")
    audit_path.write_text(json.dumps(audit,indent=2,ensure_ascii=False)+"\n","utf-8")
    # Re-hash exact 56 sources after writing the staged files and manifests.
    for key,entry in manifest["files"].items():
        data=(base/entry["path"]).read_bytes()
        if (len(data)!=entry["bytes"] or
            sha256(data).hexdigest()!=entry["sha256"] or
            layout["source_sha256_by_subject_year"][key]!=entry["sha256"]):
            raise ValueError("Post-update PDF/cover hash mismatch: "+key)
    print("NATIVE_HEADERS_PI_ARAB_EN_15_PDF_56_MANIFEST_VERIFIED",
          json.dumps({"count":15,"untouched":41,
                      "total_pdp":audit["total_lessons_pdp"],
                      "source_links":audit["total_source_links"],
                      "total_pages":manifest["pages"]},ensure_ascii=False))
    return audit


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--sources",required=True)
    parser.add_argument("--assets",default="rpt_2027/web_2027_pdfs")
    parser.add_argument("--run-english",type=int,required=True)
    parser.add_argument("--run-arabpi",type=int,required=True)
    args=parser.parse_args()
    install(args.sources,args.assets,run_english=args.run_english,
            run_arabpi=args.run_arabpi)
