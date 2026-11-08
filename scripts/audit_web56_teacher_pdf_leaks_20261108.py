"""Audit the EXACT 56 PDF files served by Web's /api/rpt/2027/all route.

This is read-only: no profile, DB, billing, Telegram, or PDFs are modified.
All files must match the active manifest before any leak count is trusted.
Absence of detected developer text is NOT academic signoff.
"""
from __future__ import annotations
import argparse
from collections import Counter
from hashlib import sha256
import json
from pathlib import Path
import re
from scripts.audit_rpt2027_teacher_text_leaks_20261108 import scan_paths

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"rpt_2027/web_2027_pdfs"
REPORT=ROOT/"staging/web56_teacher_leaks_20261108/report.json"

def audit(root=CATALOG):
    base=Path(root)
    manifest_file=base/"manifest.json"
    src=json.loads(manifest_file.read_text(encoding="utf-8"))
    if (src.get("version")!=1 or src.get("count")!=56
        or src.get("year")!=2027
        or src.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
        or src.get("academic_final_approved") is not False):
        raise ValueError("Unexpected Web RPT draft manifest / academic approval")
    items=src.get("files")
    if not isinstance(items,dict) or len(items)!=56:
        raise ValueError("Incomplete Web RPT 56-PDF manifest")
    files=[]
    discrepancy=[]
    by_subject=Counter()
    for key,entry in sorted(items.items()):
        if not re.fullmatch(r"[a-z_]+:[2-6]",key):
            raise ValueError("Invalid RPT pair "+repr(key))
        subject,year=key.split(":")
        if entry.get("path")!=f"{subject}/tahun_{year}.pdf":
            raise ValueError("Manifest subject/year path mismatch "+key)
        path=base/entry["path"]
        if path.is_symlink() or not path.is_file():
            discrepancy.append({"pair":key,"error":"missing or symlinked"})
            continue
        content=path.read_bytes()
        if (len(content)!=entry.get("bytes")
            or sha256(content).hexdigest()!=entry.get("sha256")
            or not content.startswith(b"%PDF-")):
            discrepancy.append({"pair":key,"error":"PDF/manifest hash, bytes or header mismatch"})
            continue
        if not 8_000<=len(content)<=25*1024*1024:
            discrepancy.append({"pair":key,"error":"out-of-range PDF size"})
            continue
        files.append(path)
        by_subject[subject]+=1
    result=scan_paths(files,pdf_only=True)
    result.update({
        "source":"actual_web_pdf_catalog_not_legacy_telegram",
        "manifest_sha256":sha256(manifest_file.read_bytes()).hexdigest(),
        "target_count":56,
        "manifest_discrepancies":discrepancy,
        "subjects":dict(sorted(by_subject.items())),
        "academic_signoff":False,
        "ready_for_production":False,
    })
    if result["scanned_files"]!=56:
        discrepancy.append({"error":"not all 56 PDFs were scanned"})
    return result

def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output",default=str(REPORT))
    parser.add_argument("--fail-on-findings",action="store_true")
    args=parser.parse_args(argv)
    report=audit()
    path=Path(args.output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="findings"},ensure_ascii=False,indent=2))
    for hit in report["findings"][:80]:
        print(f'{hit["file"]} p{hit["page"]}: {hit["rule"]}: {hit["match"]}')
    return int(bool(report["manifest_discrepancies"] or report["read_errors"]
                    or report["scanned_files"]!=56
                    or (args.fail_on_findings and report["findings_count"])))

if __name__=="__main__":
    raise SystemExit(main())