"""Check Year3 PI RPH SP codes against original textbook footer codes.

Book source: user's Drive GuruBesar_BukuTeks_Pendidikan_Islam_T3_SK.pdf
(85 PDF pages, SHA-256 pinned). 83 distinct 3-part SP codes extracted from
the book PDF text layer. This verifies code presence somewhere in the book,
NOT each lesson/printed page, exact SP wording, or official DSKP alignment.

One exception: SP6.4.3 used in T3-L146 is visibly present in the Year3 DSKP
(PDF p51, printed p39), although its code was not found in textbook footer
text (printed pp140-146 inspected). Do NOT delete or fabricate this SP.

No source PDFs are mirrored to GitHub; all evidence lives in editor metadata.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import json
import re
from pathlib import Path

from pi_quality_audit import ROOT

BOOK_DRIVE_ID = "1DNXL1vmN3ERz6o4_7jcCVc9m3E42JDSY"
BOOK_SHA256 = "fcc36cbe9ed64aa7d8cbf17dbf105b73c2e34e4fc988e65d63a12fa2386a4f17"
DSKP_DRIVE_ID = "1tjcWRrfcAGk-Y_OpzeQhO253hunaz9RA"
DSKP_SHA256 = "6e0a7b58cfb88c8761290c53245958ab940583e61f1cdaa1d5e615c48f32f5af"
BOOK_CODE_PREFIXES = {
    "1.1": 2, "1.2": 2, "1.3": 2, "1.4": 2, "1.5": 5, "1.6": 3,
    "2.1": 6,
    "3.1": 4, "3.2": 5,
    "4.1": 7, "4.2": 2, "4.3": 5,
    "5.1": 5, "5.2": 3, "5.3": 5,
    "6.1": 5, "6.2": 5, "6.3": 5,
    "7.1": 2, "7.2": 2, "7.3": 2,
}
BOOK_CODE_64 = ("6.4.1","6.4.2","6.4.4","6.4.5")
SP_RE=re.compile(r"(?<![0-9])([1-9]\.\d{1,2}\.\d{1,2})(?![0-9])")
CSV_FIELDS=(
    "id","year","lesson","sp_codes","category","missing_book_footer_codes",
    "source_book_code_presence_only","dskp_6433_manual_visual_reference",
    "objective_2_needs_sp_alignment_review","source_material_original_preserved",
    "content_expert_approved","book_exercise_page_verified",
    "full_dskp_text_alignment_verified","can_publish","release"
)


def index():
    codes=set(BOOK_CODE_64)
    for prefix, top in BOOK_CODE_PREFIXES.items():
        codes.update(prefix+"."+str(n) for n in range(1,top+1))
    assert len(codes)==83
    assert "6.4.3" not in codes and "2.1.4" in codes
    return codes


def audit(root=ROOT):
    codebook=index()
    src=json.loads((Path(root)/"year3.json").read_text(encoding="utf-8"))
    assert src["year"]==3 and src["ready"] is False and len(src["records"])==147
    rows=[];used=set();exceptions=[]
    for r in src["records"]:
        assert r["withheld"] is False and r["verified_ready"] is False
        sp=r["fields"]["sp"]
        codes=list(dict.fromkeys(SP_RE.findall(sp)))
        used.update(codes)
        absent=[code for code in codes if code not in codebook]
        if not codes:
            category="QURAN_TASMI_NO_THREE_LEVEL_SP"
            assert "سورة" in sp and "staging_source_sp6433_review" not in r
        elif absent:
            category="MISSING_FROM_BOOK_FOOTER_MANUAL_DSKP_CHECK"
            assert r["id"]=="T3-L146" and absent==["6.4.3"]
            record=r.get("staging_source_sp6433_review")
            assert record is not None and record["publication"]=="HOLD"
            assert record["evidence_id"]=="PI-T3-DKSP6433-TB142-146-20261107"
            assert record["dskp_drive_id"]==DSKP_DRIVE_ID
            assert record["dskp_sha256"]==DSKP_SHA256
            assert record["dskp_pdf_page"]==51 and record["dskp_printed_page"]==39
            assert record["dskp_sp_6_4_3_visually_present"] is True
            assert record["book_drive_id"]==BOOK_DRIVE_ID
            assert record["book_sha256"]==BOOK_SHA256
            assert record["book_footer_code_6_4_3_present"] is False
            assert record["book_printed_pages_examined"]==[142,143,144,145,146]
            assert record["book_pdf_pages_examined"]==[83,84,85]
            assert record["objective_second_statement_review_required"] is True
            assert record["source_sk_sp_text_unchanged"] is True
            assert record["specific_lesson_exercise_approved"] is False
            assert record["content_expert_approved"] is False
            assert record["jawi_editor_approved"] is False
            orig=record["original_materials_preserved"]
            assert r["fields"]["bahan"].split("\n",1)[1]==orig.split("\n",1)[1]
            assert r["fields"]["bahan"].split("\n",1)[0]==record["new_materials_first_line"]
            assert "6.4.3" in sp and "6.4.4" in sp
            assert "2. مثنارايكن كڤنتيڠن" in r["fields"]["objektif"]
            assert "6.4.4 مروموس كڤنتيڠن" in sp
            exceptions.append(r["id"])
        else:
            category="ALL_CODES_PRESENT_IN_ORIGINAL_BOOK_FOOTERS"
        rows.append({
            "id":r["id"],"year":3,"lesson":r["lesson"],
            "sp_codes":"|".join(codes),"category":category,
            "missing_book_footer_codes":"|".join(absent),
            "source_book_code_presence_only":bool(codes and not absent),
            "dskp_6433_manual_visual_reference":bool(absent),
            "objective_2_needs_sp_alignment_review":bool(absent),
            "source_material_original_preserved":bool(absent),
            "content_expert_approved":False,
            "book_exercise_page_verified":False,
            "full_dskp_text_alignment_verified":False,
            "can_publish":False,
            "release":"NO_GO",
        })
    count=Counter(r["category"] for r in rows)
    assert len(rows)==147 and len(used)==83
    assert count["ALL_CODES_PRESENT_IN_ORIGINAL_BOOK_FOOTERS"]==109
    assert count["MISSING_FROM_BOOK_FOOTER_MANUAL_DSKP_CHECK"]==1
    assert count["QURAN_TASMI_NO_THREE_LEVEL_SP"]==37
    assert exceptions==["T3-L146"]
    assert sum(len(r["sp_codes"].split("|")) for r in rows if r["sp_codes"])==177
    return {
        "purpose":"Year3 textbook code-footers preflight; not official DSKP accreditation",
        "book_drive_id":BOOK_DRIVE_ID,
        "book_sha256":BOOK_SHA256,
        "book_pdf_pages":85,
        "unique_source_book_sp_codes":len(codebook),
        "year3_total_draft_lessons":147,
        "year3_lessons_with_book_footer_code_present":109,
        "year3_lessons_with_book_footer_code_not_observed":1,
        "missing_footer_code":"6.4.3",
        "missing_footer_lesson_ids":exceptions,
        "dskp_6433_visually_confirmed":True,
        "dskp_pdf_page":51,
        "dskp_printed_page":39,
        "tasmi_verse_based_lessons_without_three_level_sp":37,
        "distinct_year3_codes_used":len(used),
        "source_sp_code_occurrences":177,
        "individual_exercise_page_approved":0,
        "content_expert_approved":0,
        "can_publish":False,
        "release":"NO_GO",
        "rows":rows
    }


def write(json_path,csv_path,root=ROOT):
    r=audit(root)
    Path(json_path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with Path(csv_path).open("w",encoding="utf-8-sig",newline="") as dest:
        writer=csv.DictWriter(dest,fieldnames=CSV_FIELDS)
        writer.writeheader();writer.writerows(r["rows"])
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},ensure_ascii=False,indent=2))


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--json",required=True)
    parser.add_argument("--csv",required=True)
    a=parser.parse_args()
    write(a.json,a.csv)
