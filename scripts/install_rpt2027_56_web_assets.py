"""Install exactly 56 CI-produced DRAF RPT PDFs into Web's private local catalog.

Only read source GitHub Actions artifacts from the already green PR #441.
Never generate or invent RPT content, upload publicly, charge credits, touch
school records, merge any source PR or change Telegram.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path

SOURCE_COUNTS={"english":5,"math":5,"four":20,"twentyone":21,"sains":5}
SUBJECTS={
    "ENGLISH":"english","MATEMATIK":"matematik","BAHASA_ARAB":"bahasa_arab",
    "BAHASA_MELAYU":"bahasa_melayu","MUZIK":"muzik",
    "PENDIDIKAN_ISLAM":"pendidikan_islam","MORAL":"pendidikan_moral",
    "PJPK":"pjpk","PSV":"psv","RBT":"rbt","SEJARAH":"sejarah","SAINS":"sains",
}
EXPECTED={
    f"{subject}:{year}"
    for subject in SUBJECTS.values()
    for year in ((4,5,6) if subject in ("rbt","sejarah") else (2,3,4,5,6))
}
RE=re.compile(r"^CIKGULAJU_RPT_([A-Z_]+)_TAHUN_([2-6])_2027_.*\.pdf$")
RUNS={
    "english":42395310599,"math":42395310640,"four":42395310661,
    "twentyone":42395310597,"sains":42395310498,
}
ARTIFACT_NAMES={
    "english":"RPT2027-ENGLISH-Y2Y6-800-LIMA-LAJUR-DRAF",
    "math":"RPT2027-MATH-585-LESSON-5-LIMA-LAJUR-DRAF",
    "four":"RPT2027-20-BM-PI-ARAB-MUZIK-Seragam-DRAF",
    "twentyone":"RPT2027-21-asal-dan-3-RBT-simulasi-DRAF",
    "sains":"RPT2027-SAINS-342-PDP-PROPOSAL-FIVE-COLUMN-PARTIAL-DRAF",
}

def source_files(artifacts):
    root=Path(artifacts)
    matches={}
    for name,expected_count in SOURCE_COUNTS.items():
        directory=root/name
        if not directory.is_dir():
            raise ValueError("Missing GitHub Actions source group: "+name)
        candidates=list(directory.rglob("*.pdf"))
        group={}
        for file in candidates:
            # Keep exactly the source RPT folder; explicitly exclude 3 RBT
            # simulations (same naming pattern but not a classroom RPT).
            if name=="twentyone" and file.parent.name!="pdf":
                continue
            if name=="sains" and file.parent.name!="sains_342_pdp_SEPARA_DRAF":
                continue
            m=RE.fullmatch(file.name)
            if not m:
                continue
            code=SUBJECTS.get(m.group(1))
            if code is None:
                raise ValueError("Unknown subject in published RPT source: "+file.name)
            year=int(m.group(2))
            if name=="english" and code!="english" or \
               name=="math" and code!="matematik" or \
               name=="four" and code not in ("bahasa_melayu","pendidikan_islam","bahasa_arab","muzik") or \
               name=="twentyone" and code not in ("pendidikan_moral","pjpk","psv","rbt","sejarah") or \
               name=="sains" and code!="sains":
                raise ValueError("Untrusted subject in GitHub Actions artifact group")
            key=f"{code}:{year}"
            if key in matches or key in group:
                raise ValueError("Duplicate RPT subject/year "+key)
            group[key]=file
        if len(group)!=expected_count:
            raise ValueError(f"Incorrect {name} source count: {len(group)} not {expected_count}")
        matches.update(group)
    if set(matches)!=EXPECTED or len(matches)!=56:
        raise ValueError("Not a complete authorized 12-subject, 56-PDF catalog")
    return matches

def install(artifacts,output):
    import fitz
    files=source_files(artifacts)
    base=Path(output)
    if base.exists() and any(base.iterdir()):
        # Repeated PR QA must be idempotent. No overwrites of existing PDFs.
        # Accept a complete catalog only when all 56 bytes still equal the
        # five immutable CI sources; otherwise FAIL rather than overwrite.
        manifest_file=base/"manifest.json"
        if not manifest_file.is_file() or manifest_file.is_symlink():
            raise ValueError("Existing RPT folder has no trustworthy manifest")
        old=json.loads(manifest_file.read_text("utf-8"))
        if (old.get("version")!=1 or old.get("count")!=56
            or old.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
            or set(old.get("files",{}))!=EXPECTED):
            raise ValueError("Existing 56-PDF manifest incompatible")
        for key,source in files.items():
            code,year=key.split(":")
            entry=old["files"][key]
            rel=f"{code}/tahun_{year}.pdf"
            dest=base/rel
            if (entry.get("path")!=rel or not dest.is_file()
                or dest.is_symlink()
                or hashlib.sha256(dest.read_bytes()).hexdigest()!=hashlib.sha256(source.read_bytes()).hexdigest()
                or dest.stat().st_size!=entry.get("bytes")):
                raise ValueError("Existing PDF differs from original CI source: "+key)
        return old
    base.mkdir(parents=True,exist_ok=True)
    entries={}
    pages=0
    for key,source in sorted(files.items()):
        code,year=key.split(":")
        data=source.read_bytes()
        if not 8_000<=len(data)<=25*1024*1024 or not data.startswith(b"%PDF-"):
            raise ValueError("Unusable PDF source "+key)
        try:
            with fitz.open(stream=data,filetype="pdf") as doc:
                if not 2<=doc.page_count<=300:
                    raise ValueError("Page count invalid: "+key)
                if not all(p.rect.width>p.rect.height for p in doc):
                    raise ValueError("RPT must be landscape: "+key)
                cover=doc[0].get_text().upper()
                if "RPT" not in cover and "RANCANGAN" not in cover:
                    raise ValueError("RPT cover absent: "+key)
                count=doc.page_count
        except (RuntimeError,ValueError) as exc:
            raise ValueError("RPT failed PDF verification: "+key) from exc
        rel=f"{code}/tahun_{year}.pdf"
        target=base/rel
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_bytes(data)
        entries[key]={
            "path":rel,"sha256":hashlib.sha256(data).hexdigest(),
            "bytes":len(data),"pages":count,"status":"DRAF",
            "source_run_id":RUNS[next(src for src in SOURCE_COUNTS if Path(artifacts,src) in source.parents)],
        }
        pages+=count
    manifest={
        "version":1,"year":2027,
        "status":"DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL",
        "count":56,"pages":pages,
        "files":entries,
        "source":"Five successful GitHub Actions RPT 2027 CI artifacts from CikguLaju PR #441, fixed run IDs",
        "ready_for_web_catalog":True,
        "academic_final_approved":False,
        "free_rph_quota_charged":False,
        "telegram_production_database_modified":False,
        "warning":"All DRAF. Academic SK/SP, textbook alignment and class timetable must be reviewed by teacher.",
    }
    (base/"manifest.json").write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+"\n","utf-8")
    return manifest

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--artifacts",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=install(args.artifacts,args.output)
    print("RPT_2027_56_PDF_CATALOG_STAGED",result["count"],"PDF",result["pages"],"pages")
