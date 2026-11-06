#!/usr/bin/env python3
"""Prove the Sejarah FINAL_READY path is achievable using a fake temp-only approval.

This creates a positive, *fictional* approval in a throwaway directory.
No original source, human approval record, production or staging state is updated.
"""
import csv
import json
from pathlib import Path
import re
import shutil
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from web.sejarah_2027_staging_source import (
    SejarahNotReady, lesson, source_fingerprint, source_paths,
)
from web.rph_shared_source_identity import source_fingerprint as shared

def expect_denied(root):
    try:
        lesson(4,1,root=root)
    except SejarahNotReady:
        return
    raise AssertionError("Incomplete approval unexpectedly passed")

with tempfile.TemporaryDirectory(prefix="sejarah-fake-ready-") as td:
    target=Path(td)
    for n in (1,2):
        for rel in source_paths(4,n):
            src=ROOT/rel;dest=target/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            if not dest.exists(): shutil.copy2(src,dest)
    manifest_rel="audits/sejarah_y4_y6_release_approval_manifest_20261106.json"
    approval_path=target/manifest_rel
    approval_path.parent.mkdir(parents=True,exist_ok=True)
    shutil.copy2(ROOT/manifest_rel,approval_path)

    doc_path=target/"rph_standalone/sejarah/y4_2027_rph_DRAF.json"
    plan_path=target/"rpt_2027/sejarah/RPT_SEJARAH_TAHUN_4_2027_A_B_DRAF.csv"
    md_path=target/"rph_standalone/sejarah/tahun_4/RPH_SEJ-T4-PDP-001.md"

    expect_denied(target)
    doc=json.loads(doc_path.read_text(encoding="utf-8"))
    r=doc["lessons"][0]["rph"]
    r["status"]="FINAL_READY"
    r["teacher_approval"]=True
    r["textbook_page_verified"]=True
    r["textbook_reference"]["exact_activity_page_confirmed"]=True
    r["release_signoff"]={
        "approved_by":"QA_FIXTURE_ONLY_NOT_A_REAL_TEACHER",
        "web_telegram_parity_verified":True,
        "word_pdf_layout_verified":True,
    }
    doc_path.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
    expect_denied(target)

    with plan_path.open(encoding="utf-8",newline="") as fh:
        reader=csv.DictReader(fh)
        fieldnames=reader.fieldnames
        rows=list(reader)
    rows[0]["Status"]="READY"
    with plan_path.open("w",encoding="utf-8",newline="") as fh:
        writer=csv.DictWriter(fh,fieldnames=fieldnames)
        writer.writeheader();writer.writerows(rows)
    expect_denied(target)

    old_md=md_path.read_text(encoding="utf-8")
    new_md,c=re.subn(r"(?m)^\\*\\*Status:\\*\\*[^\\n]*$",
                     "**Status:** FINAL_READY",old_md,count=1)
    assert c==1,"Could not set RPH fixture status"
    md_path.write_text(new_md,encoding="utf-8")
    expect_denied(target)

    ledger=json.loads(approval_path.read_text(encoding="utf-8"))
    entry=ledger["lessons"][0]
    assert entry["id"]=="SEJ-T4-PDP-001"
    for name in (
        "release_ready","exact_textbook_exercise_page_verified",
        "teacher_individual_signoff","school_profile_logo_verified",
        "telegram_web_native_parity_verified",
    ):
        entry[name]=True
    entry["teacher_approved_by"]="QA_FIXTURE_ONLY_NOT_A_REAL_TEACHER"
    entry["textbook_evidence_url"]="https://example.invalid/fictional-visual-evidence"
    approval_path.write_text(json.dumps(ledger,ensure_ascii=False),encoding="utf-8")
    expect_denied(target)

    digest=source_fingerprint(4,1,root=target)
    assert digest==shared(4,"SEJARAH",1,root=target)
    doc["lessons"][0]["rph"]["release_signoff"]["approved_source_fingerprint"]=digest
    doc_path.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
    assert source_fingerprint(4,1,root=target)==digest,"Self-referential fingerprint"
    expect_denied(target)

    entry["approved_source_fingerprint"]=digest
    approval_path.write_text(json.dumps(ledger,ensure_ascii=False),encoding="utf-8")
    passed=lesson(4,1,root=target)
    assert passed["id"]=="SEJ-T4-PDP-001"
    assert passed["rph"]["status"]=="FINAL_READY"

    # Approving or editing the other lesson must not invalidate PdP 001.
    doc["lessons"][1]["rph"]["objective"].append("QA_OTHER_PDP_ONLY")
    doc_path.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
    assert lesson(4,1,root=target)["id"]=="SEJ-T4-PDP-001"
    # But editing the approved content must immediately close access.
    doc["lessons"][0]["rph"]["success_criteria"]+=" TAMPERED"
    doc_path.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
    expect_denied(target)

    # Restore content: a changed independent approval ledger must still deny.
    doc["lessons"][0]["rph"]["success_criteria"]=doc["lessons"][0]["rph"]["success_criteria"].removesuffix(" TAMPERED")
    doc_path.write_text(json.dumps(doc,ensure_ascii=False),encoding="utf-8")
    assert lesson(4,1,root=target)["id"]=="SEJ-T4-PDP-001"
    entry["teacher_individual_signoff"]=False
    approval_path.write_text(json.dumps(ledger,ensure_ascii=False),encoding="utf-8")
    expect_denied(target)
print("Sejarah positive READY gate fixture PASS: achievable, isolated; tampering and independent ledger denial PASS")
