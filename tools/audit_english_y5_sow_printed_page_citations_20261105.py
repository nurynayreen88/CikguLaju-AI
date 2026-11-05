"""Cross-check 160 Year5 English RPH 'printed SOW p.' citations.

The official KPM Year5 SOW is a 214-page PDF. Its printed page number is
one lower than the actual PDF 1-based page for all 160 Lesson tables. The
source PDF is not copied into GitHub: an independently inspected index of
its original pages and SHA256 is committed under audits/. Any mismatch
is reported without modifying the RPH source or hiding missing citations.
"""
from __future__ import annotations
import argparse
import json
import pathlib
import re

ROOT=pathlib.Path(__file__).resolve().parents[1]
INDEX=ROOT/"audits/english_y5_sow_160_original_printed_pages_20261105.json"
SOURCE=ROOT/"rph_standalone/english/year5"
PATTERN=re.compile(r"(?i)\\b(?:official\\s+)?SOW\\b[^\\n]{0,180}?\\bprinted\\s+p\\.\\s*(\\d{1,3})")

def run():
    data=json.loads(INDEX.read_text(encoding="utf-8"))
    actual=data["printed_pages_by_lesson_1_to_160"]
    assert len(actual)==160
    assert actual[0]==35 and actual[-1]==202
    files=sorted(SOURCE.glob("lesson_[0-9][0-9][0-9].md"))
    if len(files)!=160:
        raise ValueError(f"Expected 160 Year5 Lesson sources; found {len(files)}")
    missing=[]; matched=[]; mismatches=[]
    for lesson in range(1,161):
        fn=SOURCE/f"lesson_{lesson:03}.md"
        text=fn.read_text(encoding="utf-8")
        citations=[int(m.group(1)) for m in PATTERN.finditer(text)]
        expected=actual[lesson-1]
        if not citations:
            missing.append(lesson)
        elif any(c!=expected for c in citations):
            mismatches.append({"lesson":lesson, "expected_printed_page":expected,
                               "pdf_page":expected+1, "claimed_printed_pages":citations})
        else:
            matched.append(lesson)
    return {"total_lessons":160,"has_explicit_printed_SOW_page":160-len(missing),
            "correct_explicit_printed_pages":len(matched),
            "wrong_explicit_printed_pages":len(mismatches),
            "lessons_without_explicit_printed_page":missing,
            "mismatches":mismatches,
            "source_verified_original_pdf_sha256":data["sha256_original_pdf"],
            "editor_approval":False}

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--strict",action="store_true",
                   help="Fail when any explicitly printed SOW page is incorrect")
    opts=p.parse_args()
    report=run()
    print("ENGLISH_Y5_SOW_PRINTED_PAGE_AUDIT",json.dumps(report,sort_keys=True))
    if opts.strict and report["wrong_explicit_printed_pages"]:
        raise SystemExit(1)

if __name__=="__main__":
    main()
