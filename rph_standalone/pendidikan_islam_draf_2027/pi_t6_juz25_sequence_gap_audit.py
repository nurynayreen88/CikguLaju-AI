"""Auditable, non-destructive Juz 25 coverage of PI Year6 RPT2027.

RPT original: RPT_Pendidikan_Islam_Tahun_6_2027_CikguLaju.pdf,
Drive 1T380Ot_gG58JhxanELMM0z-gr6wmSJcL. The seven assigned
tasmi' PdPs are 002/006/010/014/018/022/026. The PdP026 tail
(Al-Ahqaf 46:1-14) belongs to Juz26, so it is NOT counted in Juz25.

Quran verse structure cross-check:
- Malaysia KDN MYQURAN juz index (Juz25: Fussilat, ash-Shura,
  az-Zukhruf, ad-Dukhan, al-Jathiyah; Juz26 starts in al-Jathiyah).
  https://qurankdn.moha.gov.my/myquran/index.php/juzuk/index
- Quran.com surah index for verse totals:
  https://quran.com/ms/surahs
- Independent Juz25 verse-count crosscheck (246 ayat):
  https://www.amalkit.com/quran/juz-25

This is a gap inventory, NOT an authorized Quran recitation redistribution,
teacher assignment, official DSKP code mapping, or revision to the RPT.
Neither RPT original nor held RPH catalog fields are changed.
"""
from __future__ import annotations
import argparse
import csv
import json
from pathlib import Path

from pi_quality_audit import ROOT

RPT_DRIVE_ID="1T380Ot_gG58JhxanELMM0z-gr6wmSJcL"
RPT_SHA256="b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b"
# Quran structure per Juz25: 41:47-54, 42:1-53, 43:1-89, 44:1-59, 45:1-37.
JUZ25={41:(47,54),42:(1,53),43:(1,89),44:(1,59),45:(1,37)}
ASSIGNED={
    "T6-L002": ((42,1,32),),
    "T6-L006": ((42,33,51),),
    "T6-L010": ((42,52,53),(43,1,33)),
    "T6-L014": ((43,34,73),),
    "T6-L018": ((44,40,59),),
    "T6-L022": ((45,1,22),),
    "T6-L026": ((45,23,33),(46,1,14)),
}
SOURCE_TEXT_CUES={
    "T6-L002": ("الشورى", "1-32"),
    "T6-L010": ("الشورى", "52-53", "الزخرف", "1-33"),
    "T6-L022": ("الجاثية", "1-22"),
    "T6-L026": ("الجاثية", "23-33", "الاحقاڤ", "1-14"),
}
HELD={"T6-L006","T6-L014","T6-L018"}
CSV_FIELDS=("surah_number","missing_first_ayah","missing_last_ayah",
            "missing_ayah_count","source_mapping_status",
            "automatically_assigned_to_pdp","teacher_or_expert_approved",
            "release")


def spans(values):
    """Collapse sorted uncovered ayah numbers into maximal inclusive ranges."""
    vals=sorted(set(values))
    if not vals:
        return []
    groups=[]
    start=last=vals[0]
    for value in vals[1:]:
        if value==last+1:
            last=value
        else:
            groups.append((start,last))
            start=last=value
    groups.append((start,last))
    return groups


def audit(root=ROOT):
    r=json.loads((Path(root)/"year6.json").read_text(encoding="utf-8"))
    assert r["year"]==6 and r["ready"] is False and len(r["records"])==143
    assert sum(end-start+1 for start,end in JUZ25.values())==246
    observed=set()
    for lesson, intervals in ASSIGNED.items():
        num=int(lesson[-3:])
        row=r["records"][num-1]
        assert row["id"]==lesson and row["lesson"]==num
        assert row["verified_ready"] is False
        if lesson in HELD:
            assert row["withheld"] is True and row["state"]=="TAHAN_SEMAKAN_KANDUNGAN"
            assert "fields" not in row and "intro" not in row
        else:
            assert row["withheld"] is False
            source=row["fields"]["sp"]
            for text in SOURCE_TEXT_CUES[lesson]:
                assert text in source, (lesson,text)
        for surah,first,last in intervals:
            assert first>=1 and last>=first
            if surah not in JUZ25:
                assert lesson=="T6-L026" and (surah,first,last)==(46,1,14)
                continue
            lower,upper=JUZ25[surah]
            assert lower<=first<=last<=upper,(lesson,surah,first,last)
            for verse in range(first,last+1):
                token=(surah,verse)
                assert token not in observed, ("duplicate",token)
                observed.add(token)
    complete={(surah,verse) for surah,(first,last) in JUZ25.items()
              for verse in range(first,last+1)}
    gaps=sorted(complete-observed)
    grouped={surah:spans(verse for s,verse in gaps if s==surah)
             for surah in JUZ25}
    missing=[{"surah_number":surah,
              "missing_first_ayah":first,"missing_last_ayah":last,
              "missing_ayah_count":last-first+1,
              "source_mapping_status":"NOT_MENTIONED_IN_RPT2027_JUZ25_TASMI_SEQUENCE",
              "automatically_assigned_to_pdp":False,
              "teacher_or_expert_approved":False,
              "release":"NO_GO"}
              for surah,blocks in grouped.items()
              for first,last in blocks]
    assert [(x["surah_number"],x["missing_first_ayah"],x["missing_last_ayah"],
             x["missing_ayah_count"]) for x in missing]==[
        (41,47,54,8),(43,74,89,16),(44,1,39,39),(45,34,37,4)
    ]
    assert len(observed)==179 and len(gaps)==67 and len(missing)==4
    assert not (set(gaps)&observed)
    assert sorted(ASSIGNED)==sorted(["T6-L002","T6-L006","T6-L010",
                                      "T6-L014","T6-L018","T6-L022","T6-L026"])
    return {
        "purpose":"Full original Juz25 sequence completeness check; DO NOT reassign ayat silently",
        "rpt_drive_id":RPT_DRIVE_ID,"rpt_sha256":RPT_SHA256,
        "original_rpt_pdp_ids":list(ASSIGNED),
        "original_rpt_pdp_count":len(ASSIGNED),
        "juz25_expected_ayah_count":246,
        "juz25_ayah_assigned_in_rpt":179,
        "juz25_ayah_missing_in_rpt":67,
        "juz25_missing_non_overlapping_blocks":4,
        "missing_fussilat":8,"missing_zukhruf":16,
        "missing_dukhan":39,"missing_jathiyah":4,
        "juz26_pdp026_ahqaf_ayat_not_counted_as_juz25":14,
        "original_held_rph_source_records_preserved":3,
        "automatic_verse_reassignments":0,
        "exact_tasmi_teacher_assignments_approved":0,
        "source_quran_juz_index":"https://qurankdn.moha.gov.my/myquran/index.php/juzuk/index",
        "source_quran_surah_verse_counts":"https://quran.com/ms/surahs",
        "rpt_proposed_gap_resolution":"EDITOR_TEACHER_DECISION_REQUIRED",
        "expert_quran_sequence_approvals":0,
        "can_publish":False,
        "release":"NO_GO",
        "rows":missing,
    }


def write(json_path,csv_path,root=ROOT):
    r=audit(root)
    Path(json_path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",
                               encoding="utf-8")
    with Path(csv_path).open("w",encoding="utf-8-sig",newline="") as out:
        writer=csv.DictWriter(out,fieldnames=CSV_FIELDS)
        writer.writeheader();writer.writerows(r["rows"])
    print(json.dumps({k:v for k,v in r.items() if k!="rows"},
                     ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--json",required=True);p.add_argument("--csv",required=True)
    args=p.parse_args();write(args.json,args.csv)
