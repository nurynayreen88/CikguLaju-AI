"""Prepare non-destructive clean PDF replacements for the 56-file Web draft catalog.

Requires the fully tested PR #441 source-preview PDF directory. Outputs to
an ISOLATED staging folder only; never overwrites production PDF assets.
The source files and all academic HOLD records remain available for audit.
"""
from __future__ import annotations
import argparse
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import re
import shutil

from scripts.audit_rpt2027_teacher_text_leaks_20261108 import scan_paths

ROOT=Path(__file__).resolve().parents[1]
WEB=ROOT/"rpt_2027/web_2027_pdfs"
DEFAULT_SOURCE=ROOT/"staging/rpt_2027_seragam_2026"
DEFAULT_DEST=ROOT/"staging/web56_teacher_leaks_20261108/clean_catalog"

NAME=re.compile(r"^CIKGULAJU_RPT_(?P<subject>[A-Z_]+)_TAHUN_(?P<year>[2-6])_2027_.+\.pdf$")
ALIASES={"moral":"pendidikan_moral"}

def rects(page,term):
    return list(page.search_for(term))

def cover_preserved(original,replacement):
    import fitz
    with fitz.open(original) as a,fitz.open(replacement) as b:
        # Reject unrendered Jawi/Arabic glyphs. Missing Amiri can still yield
        # a valid PDF with Unicode U+0000 and visible placeholder squares.
        for index, page in enumerate(b):
            if chr(0) in page.get_text("text"):
                raise ValueError(f"Unmapped PDF glyph on page {index+1}: {replacement}")
        def pdp_ids(document):
            source=" ".join(page.get_text("text") for page in document)
            pattern=(r"\b(?:SCI-Y[2-6]-PDP-\d{3}|"
                     r"(?:PJ|PK)\s+PdP\s+\d{3}|"
                     r"(?:PdP|Lesson)\s+\d{3})\b")
            found=re.findall(pattern,source,flags=re.IGNORECASE)
            # Teachers see "PdP 001", while SCI-Y4-PDP-001 continues to
            # exist only in the source crosswalk. Preserve the numeric
            # identity rather than requiring the old developer prefix.
            return {re.sub(r"(?i)^SCI-Y[2-6]-PDP-(\d{3})$",r"PdP \1",v)
                    for v in found}
        old_ids,new_ids=pdp_ids(a),pdp_ids(b)
        if not old_ids or old_ids!=new_ids:
            raise ValueError(f"Lesson/PdP identity mismatch: {original} "
                             f"({len(old_ids)} original vs {len(new_ids)} new)")
        if abs(a[0].rect.width-b[0].rect.width)>0.2 or abs(a[0].rect.height-b[0].rect.height)>0.2:
            raise ValueError(f"Cover/page size changed: {original}")
        if a[0].rect.width<a[0].rect.height or b[0].rect.width<b[0].rect.height:
            raise ValueError("Landscape cover required")
        results={}
        for term in ("LOGO SEKOLAH","NAMA SEKOLAH","NAMA GURU"):
            aa=rects(a[0],term);bb=rects(b[0],term)
            if len(aa)!=1 or len(bb)!=1:
                raise ValueError(f"Missing/duplicated cover field: {term} ({original})")
            diff=max(abs(getattr(aa[0],key)-getattr(bb[0],key))
                     for key in ("x0","x1","y0","y1"))
            if diff>2.5:
                raise ValueError(f"Cover field moved by {diff:.1f}pt: {original} {term}")
            results[term]=round(diff,2)
        if not 2<=b.page_count<=300 or any(p.rect.width<p.rect.height for p in b):
            raise ValueError(f"Wrong landscape/pdf page count: {replacement}")
        return {"pages_before":a.page_count,
                "pages_after":b.page_count,
                "cover_bbox_max_delta_pt":max(results.values())}

def stage(source=DEFAULT_SOURCE,dest=DEFAULT_DEST,web=WEB):
    src=Path(source)
    target=Path(dest)
    catalog=Path(web)
    source_manifest=json.loads((catalog/"manifest.json").read_text(encoding="utf-8"))
    if (source_manifest["version"]!=1 or source_manifest["count"]!=56
        or source_manifest["status"]!="DRAF_USER_VISIBLE_NOT_ACADEMIC_FINAL"
        or source_manifest["academic_final_approved"] is not False):
        raise ValueError("Unexpected source manifest")
    expected=source_manifest["files"]
    if len(expected)!=56:
        raise ValueError("Source catalog count mismatch")
    candidates={}
    for path in src.rglob("*.pdf"):
        m=NAME.fullmatch(path.name)
        if m is None:
            continue
        sub=ALIASES.get(m["subject"].lower(),m["subject"].lower())
        key=f'{sub}:{m["year"]}'
        if key not in expected:
            raise ValueError(f"Unknown replacement subject/year {path}")
        if key in candidates:
            raise ValueError(f"Duplicate replacement for {key}: {candidates[key]} + {path}")
        candidates[key]=path
    if set(candidates)!=set(expected):
        raise ValueError(f"Missing preview replacements: {sorted(set(expected)-set(candidates))}")
    # Clean target subtree is deliberately isolated and must not contain old
    # PDFs or metadata that could be mistaken for current output.
    target.mkdir(parents=True,exist_ok=True)
    if list(target.rglob("*.pdf")):
        raise ValueError("Candidate output folder is not empty")
    manifest=deepcopy(source_manifest)
    cover_meta=json.loads((catalog/"original_cover_layout_verified.json").read_text(encoding="utf-8"))
    positions={}
    generated=[]
    for key in sorted(expected):
        entry=manifest["files"][key]
        old=catalog/entry["path"]
        new=candidates[key]
        positions[key]=cover_preserved(old,new)
        dst=target/entry["path"]
        dst.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(new,dst)
        data=dst.read_bytes()
        entry["sha256"]=sha256(data).hexdigest()
        entry["bytes"]=len(data)
        entry["pages"]=positions[key]["pages_after"]
        entry.pop("source_run_id",None)
        entry["source_stage"]="RPT2027_PR441_20261108_CLEAN_TEACHER_TEXT"
        cover_meta["source_sha256_by_subject_year"][key]=entry["sha256"]
        generated.append(dst)
    if set(cover_meta["source_sha256_by_subject_year"])!=set(expected):
        raise ValueError("Cover source hashes incomplete")
    result=scan_paths(generated,pdf_only=True)
    if (result["scanned_files"]!=56 or result["read_errors"] or result["findings_count"]):
        raise ValueError("Clean replacement failed developer-note gate: "+
                         str({k:result[k] for k in ("scanned_files","findings_count","read_errors")}))
    manifest["academic_final_approved"]=False
    manifest["pages"]=sum(item["pages"] for item in manifest["files"].values())
    manifest["source"]="Pinned PR441 commit 514f562b95867b8f6954d169b9397a3c2af2e144; teacher-display cleanup rebuilt 2026-11-08"
    native=manifest.get("native_table_headings_pi_arab_english_20261108")
    if isinstance(native,dict):
        native["other_pdf_files_unchanged"]=0
        native["original_cover_preserved"]=True
        native["cleanup_note"]="All 56 source PDFs rebuilt; official subject headings preserved"
    manifest["ready_for_web_catalog"]=True  # Same existing user-visible DRAF state.
    manifest["source_projection"]="PR441_TEXT_ONLY_REVIEW_CLEANUP_NOT_ACADEMIC_SIGNOFF"
    (target/"manifest.json").write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",
                                        encoding="utf-8")
    (target/"original_cover_layout_verified.json").write_text(
        json.dumps(cover_meta,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    evidence={
        "clean_pdf_count":56,
        "original_pdf_count":len(expected),
        "not_academic_final":True,
        "source_assets_mutated":False,
        "all_cover_fields_same_positions_within_2_5pt":True,
        "layout_comparison":positions,
        "new_manifest_sha256":sha256((target/"manifest.json").read_bytes()).hexdigest(),
        "source_pdf_text_audit":{"scanned_files":result["scanned_files"],
                                  "findings_count":result["findings_count"],
                                  "read_errors":result["read_errors"]},
    }
    (target/"clean_candidate_audit.json").write_text(
        json.dumps(evidence,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return evidence

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source",default=str(DEFAULT_SOURCE))
    p.add_argument("--dest",default=str(DEFAULT_DEST))
    args=p.parse_args()
    print(json.dumps(stage(args.source,args.dest),ensure_ascii=False,indent=2))

if __name__=="__main__":
    main()