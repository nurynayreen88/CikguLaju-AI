"""Audit the *actual packaged* RPT PDFs selected by Web/Telegram.

Does not claim academic approval, rewrite PDFs, or change source hashes.
Missing dynamic Moral/PSV files are identified separately instead of silently
claiming they were scanned. No files are ever modified.
"""
from __future__ import annotations
import json
import sys
from pathlib import Path
from scripts.audit_rpt2027_teacher_text_leaks_20261108 import scan_paths

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"staging/rpt_2027_seragam_2026/packaged_delivery_pdf_audit.json"
SUBJECTS={
  "english":("english","RPT_ENGLISH_TAHUN_%d_2027_UNTUK_GURU.pdf"),
  "bahasa_melayu":("bahasa_melayu","RPT_Bahasa_Melayu_Tahun_%d_2027_DRAF.pdf"),
  "matematik":("matematik","RPT_Matematik_Tahun_%d_2027_v28_SEMENTARA.pdf"),
  "pendidikan_islam":("pendidikan_islam","RPT_Pendidikan_Islam_Tahun_%d_2027_CikguLaju.pdf"),
  "pjpk":("pjpk","RPT_PJPK_Tahun_%d_2027_DRAF.pdf"),
}
DYNAMIC_ROUTING={
  "pendidikan_moral":"Generated/combined PDF, test actual generator separately",
  "psv":"Generated-on-demand PDF, test actual generator separately",
}

def run(root=ROOT, output=OUT):
    base=Path(root)
    paths=[]
    for subject,(folder,pattern) in SUBJECTS.items():
        for year in range(2,7):
            p=base/"rpt_2027"/folder/(pattern%year)
            paths.append(p)
    missing=[str(p.relative_to(base)) for p in paths if not p.is_file()]
    report=scan_paths(paths,pdf_only=True)
    report["target_count"]=len(paths)
    report["missing_packaged_files"]=missing
    report["dynamic_routes_outside_scope"]=DYNAMIC_ROUTING
    report["academic_signoff"]=False
    report["ready_for_production"]=False
    path=Path(output)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="findings"},ensure_ascii=False,indent=2))
    for entry in report["findings"][:65]:
        print(f'{entry["file"]} p.{entry["page"]}: {entry["rule"]}: {entry["match"]}')
    # Audit must have 25 readable PDFs; findings are not release approved.
    if missing or report["read_errors"] or report["scanned_files"]!=len(paths):
        return 2
    return 0

if __name__=="__main__":
    raise SystemExit(run())
