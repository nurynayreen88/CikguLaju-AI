"""Independent tasmi' source-continuity and heavy-recitation review, Years 2–6.

Uses all 114 Quran.com chapter lengths and every explicit tasmi' SP range.
Gaps in six HELD records are not patched or treated as teacher-ready.
A zero gap *between first and last referenced verse* does NOT certify an
entire Juz/RPT/year's coverage, Quran teaching, or official DSKP codes.
"""
from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path

from pi_quality_audit import COUNT,HELD,ROOT
from pi_quran_114_surah_range_audit import QURAN_114,normal,parse
from pi_t6_juz25_sequence_gap_audit import audit as juz25_audit

def global_offsets():
    entries=[pair.split(":") for pair in QURAN_114.split()]
    assert len(entries)==114
    out={}
    pos=0
    for i,(name,count) in enumerate(entries,1):
        name=normal(name.replace("_"," "))
        assert name not in out
        out[name]={"chapter":i,"offset":pos,"max":int(count)}
        pos+=int(count)
    assert pos==6236
    for alias,canonical in {
        "النباء":"النبأ",
        "الصاڤات":"الصافات",
        "سباء":"سبأ",
        "الاحقاڤ":"الأحقاف",
    }.items():
        out[normal(alias)]=out[normal(canonical)]
    return out


def audit(root=ROOT):
    root=Path(root)
    offsets=global_offsets()
    by_year=[]
    heavy=[]
    for year,total in COUNT.items():
        catalog=json.loads((root/f"year{year}.json").read_text(encoding="utf-8"))
        assert len(catalog["records"])==total and catalog["ready"] is False
        covered={}
        entries=[]
        unbounded=[]
        for row in catalog["records"]:
            if row["withheld"]:
                assert (year,row["lesson"]) in HELD
                continue
            assert row["verified_ready"] is False
            f=row["fields"]
            if "تسميع" not in f["sk"] and "ختم القرءان" not in f["sk"]:
                continue
            spans=parse(f["sp"])
            if not spans:
                unbounded.append(row["id"])
                continue
            lesson_ayah_count=0
            for x in spans:
                chapter=offsets[x["surah"]]
                assert 1<=x["start"]<=x["end"]<=chapter["max"],row["id"]
                lesson_ayah_count+=x["end"]-x["start"]+1
                for ayah in range(x["start"],x["end"]+1):
                    key=chapter["offset"]+ayah
                    covered.setdefault(key,[]).append(row["id"])
            if lesson_ayah_count>60:
                heavy.append({
                    "id":row["id"],"year":year,"source_range_total_ayah":lesson_ayah_count,
                    "editorial_attention":">60 AYAT in one source PdP; require teacher individual selection/tasmi timing",
                    "source_SP_not_reassigned":True,"teacher_time_approved":False,
                    "can_publish":False})
            entries.append({"id":row["id"],"source_ranges":len(spans),
                            "source_ayah_count":lesson_ayah_count})
        assert covered,(year,"zero parsed tasmi' intervals")
        duplicates=[(k,v) for k,v in covered.items() if len(v)>1]
        # Strictly no overlaps within the non-held source sequence. Overlap
        # caused by the held T2 L035 proposed ayah224 is a separate decision.
        assert not duplicates,(year,duplicates[:2])
        left,right=min(covered),max(covered)
        missing=[i for i in range(left,right+1) if i not in covered]
        expected={2:21,3:0,4:0,5:0,6:184}
        assert len(missing)==expected[year],(year,len(missing),expected[year])
        if year==6:
            assert set(unbounded)=={"T6-L137","T6-L141"},unbounded
        else:
            assert not unbounded,(year,unbounded)
        by_year.append({
            "year":year,
            "nonheld_source_tasmi_with_numeric_ranges":len(entries),
            "nonheld_source_spans":sum(x["source_ranges"] for x in entries),
            "source_ayat_mapped_between_first_and_last":len(covered),
            "missing_ayat_within_referenced_bounds":len(missing),
            "nonheld_source_verse_duplicates":len(duplicates),
            "unbounded_tasmi_lessons":unbounded,
            "full_curriculum_verified":False,
            "teacher_release":False
        })
    juz25=juz25_audit(root)
    assert juz25["juz25_ayah_missing_in_rpt"]==67
    assert any(x["id"]=="T5-L109" and x["source_range_total_ayah"]==106
               for x in heavy)
    assert len(heavy)>=10
    assert len(by_year)==5
    return {
        "source":"https://quran.com/surahs",
        "scope":"Pendidikan Islam Year2–6 source tasmi' ranges; not Jawi or full syllabus",
        "all_114_quran_chapter_positions_considered":True,
        "years_reviewed":5,
        "source_gaps_year2_l035_held_ayat225_to245":21,
        "source_juz25_original_year6_missing_ayah":67,
        "source_gaps_year6_beyond_held_and_missing_both":True,
        "year6_tasmi_l137_l141_exact_ranges_unassigned":True,
        "source_year5_saba_names_covered_including_jawi_alias":True,
        "high_volume_60plus_ayah_source_lessons_for_teacher_review":len(heavy),
        "maximum_ayah_in_one_source_pdp":max(x["source_range_total_ayah"] for x in heavy),
        "proposed_verse_assignments":0,
        "expert_approved":0,"teacher_ready":0,
        "release":"NO_GO",
        "by_year":by_year,
        "high_volume_review_queue":heavy
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    a=ap.parse_args();r=audit()
    Path(a.output).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                               encoding="utf-8")
    print(json.dumps({k:v for k,v in r.items() if k not in ("by_year","high_volume_review_queue")},
                     ensure_ascii=False,indent=2))
