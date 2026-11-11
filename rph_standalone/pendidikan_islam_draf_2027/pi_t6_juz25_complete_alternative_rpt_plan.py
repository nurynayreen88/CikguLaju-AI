"""Two mathematically complete, UNAPPROVED Quran Juz25 allocation options.

Option A adds only four missing source spans while keeping every original
Juz25 RPT passage intact; its 56/59 verse sessions trigger workload warnings.
Option B distributes 246 verses across seven sessions (35/36 each) but shifts
the original RPT boundaries. Both are editor options only, not DSKP/RPT edits.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path

from pi_quality_audit import ROOT
from pi_t6_juz25_sequence_gap_audit import ASSIGNED, JUZ25, audit as original_audit

SLOTS=("T6-L002","T6-L006","T6-L010","T6-L014",
       "T6-L018","T6-L022","T6-L026")
ADDITIONS={
    "T6-L002":((41,47,54),),
    "T6-L014":((43,74,89),),
    "T6-L018":((44,1,39),),
    "T6-L026":((45,34,37),)
}
BALANCED_LENGTHS=(35,35,35,35,35,35,36)


def flatten(spans):
    return [(surah,verse) for surah,start,end in spans
            for verse in range(start,end+1)]


def collapse(verses):
    spans=[]
    for surah,verse in verses:
        if spans and spans[-1][0]==surah and spans[-1][2]+1==verse:
            spans[-1]=(surah,spans[-1][1],verse)
        else:
            spans.append((surah,verse,verse))
    return tuple(spans)


def validate(assignment,expected_verses):
    all_verses=[]
    assert set(assignment)==set(SLOTS)
    for slot in SLOTS:
        for surah,first,last in assignment[slot]:
            assert surah in JUZ25
            assert JUZ25[surah][0]<=first<=last<=JUZ25[surah][1]
        all_verses.extend(flatten(assignment[slot]))
    assert len(all_verses)==len(set(all_verses))==len(expected_verses)==246
    assert set(all_verses)==set(expected_verses)
    return True


def plan(root=ROOT):
    source=original_audit(root)
    assert source["juz25_ayah_assigned_in_rpt"]==179
    assert source["juz25_ayah_missing_in_rpt"]==67
    expected=[(s,a) for s,(start,end) in JUZ25.items()
              for a in range(start,end+1)]
    assert len(expected)==246
    baseline={slot:tuple(span for span in ASSIGNED[slot] if span[0] in JUZ25)
              for slot in SLOTS}
    original_verses={v for seq in baseline.values() for v in flatten(seq)}
    assert len(original_verses)==179
    minimally={slot:collapse(sorted(flatten(baseline[slot])+
                    flatten(ADDITIONS.get(slot,())))) for slot in SLOTS}
    assert validate(minimally,expected)
    added=set(v for seq in minimally.values() for v in flatten(seq))-original_verses
    assert len(added)==67
    # No original Juz25 assignment may be removed from Option A.
    for slot in SLOTS:
        assert set(flatten(baseline[slot]))<=set(flatten(minimally[slot]))
    balanced={}
    offset=0
    for slot,length in zip(SLOTS,BALANCED_LENGTHS):
        balanced[slot]=collapse(expected[offset:offset+length])
        offset+=length
    assert offset==246 and validate(balanced,expected)

    def detail(assignment):
        return [{
            "pdp":slot,
            "juz25_verse_ranges":[{"surah":s,"start":a,"end":b}
                                    for s,a,b in assignment[slot]],
            "total_juz25_ayah":len(flatten(assignment[slot])),
            "student_assignment":"SELECTED_VERSES_NOT_EVERY_AYAH_BY_EVERY_STUDENT",
            "source_rpt_this_pdp_verses_preserved":set(flatten(baseline[slot]))<=set(flatten(assignment[slot])),
            "expert_and_teacher_approved":False
        } for slot in SLOTS]
    rows_a=detail(minimally)
    rows_b=detail(balanced)
    assert [r["total_juz25_ayah"] for r in rows_a]==[40,19,35,56,59,22,15]
    assert [r["total_juz25_ayah"] for r in rows_b]==list(BALANCED_LENGTHS)
    assert all(r["source_rpt_this_pdp_verses_preserved"] for r in rows_a)
    assert any(not r["source_rpt_this_pdp_verses_preserved"] for r in rows_b)
    return {
        "source_rpt_drive_id":source["rpt_drive_id"],
        "source_rpt_sha256":source["rpt_sha256"],
        "purpose":"Two source-aware Quran Juz25 redistribution OPTIONS; neither is approved",
        "source_verses_mapped":179,
        "source_verses_missing":67,
        "full_juz25_target":246,
        "source_rpt_unchanged":True,
        "held_source_rph_unchanged":True,
        "juz26_al_ahqaf_46_1_to14_not_silently_removed":True,
        "juz26_al_ahqaf_scheduling_decision_required":True,
        "official_sp_codes_assigned":0,
        "teacher_approved_plans":0,
        "academic_quality_score_percent":None,
        "editor_options":[
            {
                "name":"A_MINIMUM_SOURCE_CHANGES",
                "all_original_juz25_pdp_assignments_preserved":True,
                "all_juz25_ayah_covered_once":True,
                "heavy_pdp_for_teacher_to_split":["T6-L014","T6-L018"],
                "warning":"56 dan 59 ayat dalam slot tunggal mungkin tidak praktikal. Guru perlu pecah bacaan/tasmi atau menambah masa mengikut jadual sebenar.",
                "original_juz26_in_pdp026_still_needs_teacher_planning":True,
                "total_juz25_verses":246,
                "rows":rows_a
            },
            {
                "name":"B_BALANCED_REPLANNING",
                "all_original_juz25_pdp_assignments_preserved":False,
                "all_juz25_ayah_covered_once":True,
                "heavy_pdp_for_teacher_to_split":[],
                "warning":"Mengubah hampir semua batas PdP asal; perlu semakan pengurusan jadual dan slot bacaan Juz26 yang asalnya berkongsi PdP026.",
                "original_juz26_in_pdp026_still_needs_teacher_planning":True,
                "total_juz25_verses":246,
                "rows":rows_b
            }
        ],
        "editor_only":True,"approved_for_teacher":False,
        "publication":"HOLD","release":"NO_GO"
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    result=plan()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k!="editor_options"},ensure_ascii=False,indent=2))
