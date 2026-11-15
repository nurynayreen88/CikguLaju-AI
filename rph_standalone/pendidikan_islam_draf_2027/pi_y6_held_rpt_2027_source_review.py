"""Non-destructive source triage for all 5 wholly withheld Year 6 lessons.

RPT Pendidikan Islam Tahun 6 2027 is a teacher planning document, NOT a
validation of Mushaf ayah ranges or official DSKP wording. The source was
inspected at PDF pages 3, 5, 7, 21, 41. The original catalog remains withheld; four Quran RPH have separate Rumi
editor-only candidate proposals, without authorizing Jawi or publication.

None of the five year6 held records receives 'fields' or teacher material.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT

RPT_ID="1T380Ot_gG58JhxanELMM0z-gr6wmSJcL"
RPT_SHA="b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b"
SOURCE_CLASS="EDITOR_RPT_2027_NOT_AUTHORITATIVE_MUSHAF_OR_DSKP"
HELD_SOURCE={
    "T6-L006":{
        "rpt_pdf_page":3,"lesson_kind":"JUZ25_TASMI",
        "rpt_named_content":"الشورى اية 33–51",
        "reason":"42:33-51 is within ash-Shura chapter bounds (53 ayat) and continues from PdP002; 67 other Juz25 ayat remain unmapped. Four-step Rumi editor candidate exists; academic/tajwid and teacher time allocation not approved"},
    "T6-L014":{
        "rpt_pdf_page":5,"lesson_kind":"JUZ25_TASMI_GAP",
        "rpt_named_content":"الزخرف اية 34–73",
        "reason":"Whole Juz25 audit confirms 43:74-89 (16) and 44:1-39 (39) omitted between PdP014 and PdP018; other Juz25 gaps add 12, total 67. Candidate remains editor-only; do not silently assign missing ayat"},
    "T6-L018":{
        "rpt_pdf_page":7,"lesson_kind":"JUZ25_TASMI_GAP",
        "rpt_named_content":"الدخان اية 40–59",
        "reason":"RPT skips ad-Dukhan 44:1-39 (39 ayat) before PdP018 44:40-59; Year6 Juz25 total 67 ayat missing. Candidate still held until RPT editor assigns omitted passages"},
    "T6-L060":{
        "rpt_pdf_page":21,"lesson_kind":"PROPOSED_SICK_PRAYER_PRACTICAL",
        "rpt_named_content":"Solat ketika sakit; calon SP4.2.3–4.2.5",
        "reason":"DSKP Year6 printed p34 visually confirms SP4.2.3–4.2.5; however this separate practical PdP is explicitly a CikguLaju suggestion, not a mandated additional official Lesson. Editor candidate exists separately and awaits fiqh/Jawi review"},
    "T6-L117":{
        "rpt_pdf_page":41,"lesson_kind":"JUZ29_TASMI_MIXED_SURA",
        "rpt_named_content":"المعارج 40–44; نوح 1–28; الجن 1–13",
        "reason":"MYQURAN/Quran.com verse counts confirm PdP113→117→121 continuously covers 70:1-44, 71:1-28 and 72:1-28 (100/100), with no az-Zumar; Rumi editor candidate exists but Jawi/tajwid review still required"},
}
CSV_FIELDS=("id","rpt_pdf_page","lesson_kind","rpt_named_content","reason",
            "source_class","authoritative_mushaf_bounds_approved",
            "original_dskp_sp_approved","source_completeness_approved",
            "content_generated","can_publish","release")


def audit(root=ROOT):
    src=json.loads((Path(root)/"year6.json").read_text(encoding="utf-8"))
    assert src["year"]==6 and src["ready"] is False and len(src["records"])==143
    rows=[]
    found=set()
    for record in src["records"]:
        if record["id"] not in HELD_SOURCE:
            continue
        identity=record["id"]
        x=HELD_SOURCE[identity]
        assert identity not in found
        found.add(identity)
        assert record["withheld"] is True
        assert record["verified_ready"] is False
        assert record["state"]=="TAHAN_SEMAKAN_KANDUNGAN"
        assert "fields" not in record and "intro" not in record
        assert x["rpt_pdf_page"] in (3,5,7,21,41)
        assert x["rpt_named_content"] and x["reason"]
        rows.append({
            "id":identity,
            "rpt_pdf_page":x["rpt_pdf_page"],
            "lesson_kind":x["lesson_kind"],
            "rpt_named_content":x["rpt_named_content"],
            "reason":x["reason"],
            "source_class":SOURCE_CLASS,
            "authoritative_mushaf_bounds_approved":False,
            "original_dskp_sp_approved":False,
            "source_completeness_approved":False,
            "content_generated":False,
            "can_publish":False,
            "release":"NO_GO",
        })
    assert found==set(HELD_SOURCE) and len(rows)==5
    assert all(not row["content_generated"] and not row["can_publish"] for row in rows)
    return {
        "purpose":"Trace 5 wholly held Year6 RPH sources to RPT, without filling unsupported material",
        "rpt_drive_id":RPT_ID,
        "rpt_sha256":RPT_SHA,
        "rpt_pages_checked":[3,5,7,21,41],
        "year6_held_lessons_checked":5,
        "rpt_verse_continuity_gap_cases":2,
        "proposed_non_official_technical_pdp":1,
        "rpt_juz29_boundary_review_cases":1,
        "mushaf_source_approvals":0,
        "original_dskp_sp_approvals":0,
        "generated_held_rph":0,
        "can_publish":False,
        "release":"NO_GO",
        "rows":rows,
    }


def write(json_path,csv_path,root=ROOT):
    result=audit(root)
    Path(json_path).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    with Path(csv_path).open("w",encoding="utf-8-sig",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=CSV_FIELDS)
        writer.writeheader();writer.writerows(result["rows"])
    print(json.dumps({k:v for k,v in result.items() if k!="rows"},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json",required=True)
    p.add_argument("--csv",required=True)
    a=p.parse_args()
    write(a.json,a.csv)
