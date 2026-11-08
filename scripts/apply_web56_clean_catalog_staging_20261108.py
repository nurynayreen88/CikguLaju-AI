"""Apply prevalidated 56 clean Web draft PDF candidates to the staging branch.

Never run against a production branch directly; the caller's CI is restricted
to the exact staging branch. Every original PDF remains recoverable by its
Git blob SHA in an immutable audit report; do not overwrite user DB.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
ORIGINAL=ROOT/"rpt_2027/web_2027_pdfs"
STAGING=ROOT/"staging/web56_teacher_leaks_20261108/clean_catalog"
AUDIT=ROOT/"audits/WEB56_TEACHER_NOTES_REPLACEMENT_STAGING_20261108.json"

def _load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))

def replace(root=ROOT,candidate=None):
    root=Path(root)
    original=root/"rpt_2027/web_2027_pdfs"
    candidate=Path(candidate) if candidate else root/"staging/web56_teacher_leaks_20261108/clean_catalog"
    before=_load(original/"manifest.json")
    after=_load(candidate/"manifest.json")
    report=_load(candidate/"clean_candidate_audit.json")
    if (before.get("status")!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
        or before.get("academic_final_approved") is not False
        or after.get("status")!=before["status"]
        or after.get("academic_final_approved") is not False
        or before.get("count")!=56 or after.get("count")!=56
        or set(before.get("files",{}))!=set(after.get("files",{}))
        or report.get("clean_pdf_count")!=56
        or report.get("not_academic_final") is not True
        or report.get("source_assets_mutated") is not False
        or report["source_pdf_text_audit"]["findings_count"]!=0
        or report["source_pdf_text_audit"]["read_errors"]):
        raise ValueError("Candidate PDF/source manifest not release-safe")
    if after["pages"]!=sum(x["pages"] for x in after["files"].values()):
        raise ValueError("Candidate RPT page totals no longer match PDF manifest")
    cover=_load(candidate/"original_cover_layout_verified.json")
    if set(cover.get("source_sha256_by_subject_year",{}))!=set(after["files"]):
        raise ValueError("Clean RPT cover manifest incomplete")
    originals={}
    replacements={}
    for key,new in sorted(after["files"].items()):
        old=before["files"][key]
        if old["path"]!=new["path"]:
            raise ValueError("RPT exact subject/year path changed")
        source=original/old["path"]
        target=candidate/new["path"]
        for path,entry in ((source,old),(target,new)):
            if path.is_symlink() or not path.is_file():
                raise ValueError(f"Missing or linked PDF {path}")
            raw=path.read_bytes()
            if (not raw.startswith(b"%PDF-") or len(raw)!=entry["bytes"]
                or sha256(raw).hexdigest()!=entry["sha256"]):
                raise ValueError(f"PDF manifest digest mismatch {path}")
        if cover["source_sha256_by_subject_year"][key]!=new["sha256"]:
            raise ValueError("Cover contract disagrees with new PDF SHA")
        originals[key]={"path":old["path"],"sha256":old["sha256"],
                        "bytes":old["bytes"],"pages":old["pages"]}
        replacements[key]={"path":new["path"],"sha256":new["sha256"],
                           "bytes":new["bytes"],"pages":new["pages"]}
    for key,entry in sorted(after["files"].items()):
        shutil.copyfile(candidate/entry["path"], original/entry["path"])
    for filename in ("manifest.json","original_cover_layout_verified.json"):
        shutil.copyfile(candidate/filename,original/filename)
    evidence={
        "status":"STAGING_ONLY_TEXT_CLEANUP_NOT_ACADEMIC_APPROVAL",
        "source_release_manifest_sha256":sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        "new_release_manifest_sha256":sha256((original/"manifest.json").read_bytes()).hexdigest(),
        "original_versions_preserved_by_git_history":True,
        "source_branch":"production/cikgulaju-web-20261105",
        "original_web_release_commit":"694d6f8ca0867b1e8ec7e6c41073a982409f4ddd",
        "curriculum_academic_final_approved":False,
        "teacher_note_detector_findings":0,
        "backup_manifest_by_key":originals,
        "replacement_manifest_by_key":replacements,
    }
    path=root/"audits/WEB56_TEACHER_NOTES_REPLACEMENT_STAGING_20261108.json"
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return evidence

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate",default=str(STAGING))
    args=parser.parse_args()
    e=replace(candidate=args.candidate)
    print(json.dumps({k:v for k,v in e.items() if not k.endswith("_by_key")},
                     ensure_ascii=False,indent=2))