"""Code-presence audit against the user's DSKP PI Year 2 copy (PDF).

The DSKP PDF was inspected locally at 64 pages; these 83 SP codes and PDF
page numbers were extracted directly from its text layer and checked against
the visual p55 example for SP5.4. No copyrighted source pages are committed.

Code existence in DSKP does NOT certify that the Lesson matches the correct
wording, pedagogy, topic/book page, assessment, or Quran verses. 30 tasmi'
Lesson descriptions without an official 3-level SP code are *not* assigned
an invented code.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path

from pi_quality_audit import ROOT

SOURCE_DRIVE_ID = "1m6UG8t7tiCjLdnOo6vRj2jI4lNMniOUr"
SOURCE_SHA256 = "dd4804c118e78c5a4fed1521adf750983c6d119a310cf736b751d4994bc67dac"
SOURCE_PDF_PAGE_COUNTS = {
    "1.1": (30, 3), "1.2": (31, 3), "1.3": (33, 3),
    "1.4": (34, 3), "1.5": (36, 3), "1.6": (37, 3),
    "2.1": (39, 3), "2.2": (40, 4), "2.3": (41, 5),
    "3.1": (43, 5), "3.2": (44, 4), "3.3": (45, 4),
    "3.4": (46, 4),
    "4.1": (48, 4), "4.2": (49, 3), "4.3": (50, 4),
    "5.1": (52, 4), "5.2": (53, 4), "5.3": (54, 4), "5.4": (55, 4),
    "6.1": (57, 3), "6.2": (58, 3), "6.3": (59, 3),
}
SP_RE = re.compile(r"(?<![0-9])([1-9]\.\d{1,2}\.\d{1,2})(?![0-9])")
CSV_FIELDS = (
    "id", "year", "lesson", "category", "sp_codes", "sp_pdf_pages",
    "all_codes_present_in_original_dskp", "source_sp_text_wording_verified",
    "quran_verse_bounds_verified", "curriculum_expert_approved",
    "activity_book_pages_verified", "ready", "release"
)


def indexed_codes():
    code_pages = {}
    for prefix, (page, count) in SOURCE_PDF_PAGE_COUNTS.items():
        assert isinstance(page, int) and 1 <= page <= 64
        assert isinstance(count, int) and 1 <= count <= 8
        for n in range(1, count + 1):
            code = prefix + "." + str(n)
            if code in code_pages:
                raise ValueError("Duplicate indexed code: " + code)
            code_pages[code] = page
    assert len(code_pages) == 83
    return code_pages


def audit(root=ROOT):
    index = indexed_codes()
    data=json.loads((Path(root)/"year2.json").read_text(encoding="utf-8"))
    assert data["year"] == 2 and data["ready"] is False and len(data["records"]) == 112
    rows=[]
    seen=set()
    for record in data["records"]:
        if record["withheld"]:
            assert record["id"] == "T2-L035"
            continue
        assert record["verified_ready"] is False
        codes=list(dict.fromkeys(SP_RE.findall(record["fields"]["sp"])))
        if codes:
            category="THREE_LEVEL_DSKP_SP_CODE"
            missing=[code for code in codes if code not in index]
            if missing:
                raise ValueError("Unrecognized DSKP code: "+record["id"]+":"+repr(missing))
            seen.update(codes)
            pdf_pages={code: index[code] for code in codes}
        else:
            category="QURAN_TASMI_VERSE_RANGE_NO_THREE_LEVEL_SP"
            sp=record["fields"]["sp"]
            if "جزء" not in sp or "سورة" not in sp:
                raise ValueError("A missing DSKP code in an unexpected category: "+record["id"])
            pdf_pages={}
        rows.append({
            "id": record["id"], "year": 2, "lesson": record["lesson"],
            "category": category,
            "sp_codes": "|".join(codes),
            "sp_pdf_pages": json.dumps(pdf_pages, ensure_ascii=False),
            "all_codes_present_in_original_dskp": bool(codes),
            "source_sp_text_wording_verified": False,
            "quran_verse_bounds_verified": False,
            "curriculum_expert_approved": False,
            "activity_book_pages_verified": False,
            "ready": False,
            "release": "NO_GO",
        })
    coded=[r for r in rows if r["category"]=="THREE_LEVEL_DSKP_SP_CODE"]
    tasmi=[r for r in rows if r["category"]=="QURAN_TASMI_VERSE_RANGE_NO_THREE_LEVEL_SP"]
    assert len(rows)==111
    assert len(coded)==81 and len(tasmi)==30
    assert len(seen)==76
    assert sum(len(r["sp_codes"].split("|")) for r in coded)==192
    assert all(r["all_codes_present_in_original_dskp"] for r in coded)
    assert all(not r["all_codes_present_in_original_dskp"] for r in tasmi)
    assert all(r["release"]=="NO_GO" and not r["ready"] for r in rows)
    return {
        "purpose":"Year 2 DSKP SP code-presence only, NOT text-accuracy certification",
        "source_drive_id":SOURCE_DRIVE_ID,
        "source_sha256":SOURCE_SHA256,
        "source_pdf_pages":64,
        "indexed_dskp_sp_codes":len(index),
        "draft_lessons":len(rows),
        "coded_lessons_with_all_codes_present":len(coded),
        "coded_lessons_with_unknown_code":0,
        "distinct_codes_used":len(seen),
        "total_sp_code_occurrences":192,
        "tasmi_verse_range_lessons_without_official_3_level_sp":len(tasmi),
        "invented_official_sp_codes":0,
        "full_sp_wording_verified_lessons":0,
        "expert_approved_lessons":0,
        "academic_quality_percent":None,
        "ready":False,
        "release":"NO_GO",
        "code_to_pdf_page":index,
        "rows":rows,
    }


def write(json_path,csv_path,root=ROOT):
    d=audit(root)
    Path(json_path).write_text(json.dumps(d,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with Path(csv_path).open("w",newline="",encoding="utf-8-sig") as dst:
        w=csv.DictWriter(dst,fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(d["rows"])
    print(json.dumps({k:v for k,v in d.items() if k not in ("rows","code_to_pdf_page")},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--json",required=True)
    parser.add_argument("--csv",required=True)
    args=parser.parse_args()
    write(args.json,args.csv)
