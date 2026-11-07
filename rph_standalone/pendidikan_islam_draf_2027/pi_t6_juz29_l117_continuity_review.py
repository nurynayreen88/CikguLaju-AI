"""Juz29 Year6 L117 Quran segment continuity against neighboring RPT lessons.

Source: original Year6 PI RPT2027 (Drive) and MYQURAN KDN juz index,
Quran.com chapter verse counts. This checks ONLY al-Ma'arij (70), Nuh (71)
and al-Jinn (72) across L113/L117/L121. It does not certify all Juz29,
Arabic matan recitation, tajwid, Jawi, expert approval, or an official DSKP SP.
L117 original catalog record remains wholly WITHHELD.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from pi_quality_audit import ROOT

RPT_ID="1T380Ot_gG58JhxanELMM0z-gr6wmSJcL"
RPT_SHA="b39a07b2dd7ef6062912f12fd43e63f87a98b13bde3885c925e88a37dac70e5b"
CHAPTERS={70:(1,44),71:(1,28),72:(1,28)}
LESSONS={
    "T6-L113":((70,1,39),),
    "T6-L117":((70,40,44),(71,1,28),(72,1,13)),
    "T6-L121":((72,14,28),),
}


def audit(root=ROOT):
    src=json.loads((Path(root)/"year6.json").read_text(encoding="utf-8"))
    assert src["year"]==6 and src["ready"] is False and len(src["records"])==143
    found=set()
    for lesson,intervals in LESSONS.items():
        num=int(lesson[-3:])
        row=src["records"][num-1]
        assert row["id"]==lesson and row["lesson"]==num
        assert row["verified_ready"] is False
        if lesson=="T6-L117":
            assert row["withheld"] is True and "fields" not in row
            assert row["state"]=="TAHAN_SEMAKAN_KANDUNGAN"
        else:
            assert row["withheld"] is False
            sp=row["fields"]["sp"]
            for surah,first,last in intervals:
                assert (str(first) in sp and str(last) in sp)
                if surah==70:
                    assert "المعارج" in sp
                elif surah==72:
                    assert "الجن" in sp
        for surah,first,last in intervals:
            lower,upper=CHAPTERS[surah]
            assert lower<=first<=last<=upper
            for v in range(first,last+1):
                token=(surah,v)
                assert token not in found,token
                found.add(token)
    expected={(s,v) for s,(first,last) in CHAPTERS.items()
              for v in range(first,last+1)}
    assert len(expected)==100 and found==expected
    return {
        "purpose":"Neighboring PdP113/117/121 are continuous for Quran chapters 70-72; not full Juz29 approval",
        "rpt_drive_id":RPT_ID,"rpt_sha256":RPT_SHA,
        "pdp_ids":list(LESSONS),
        "chapter_70_al_maarij_total_ayat":44,
        "chapter_71_nuh_total_ayat":28,
        "chapter_72_al_jinn_total_ayat":28,
        "three_surahs_total_ayat":100,
        "three_surahs_mapped_ayat":100,
        "three_surahs_missing_ayat":0,
        "rpt_l117_ranges":[[70,40,44],[71,1,28],[72,1,13]],
        "continuity_before_l117":True,
        "continuity_after_l117":True,
        "az_zumar_wrong_juz29_excluded":True,
        "quran_kdn_juz_index":"https://qurankdn.moha.gov.my/myquran/index.php/juzuk/index",
        "quran_chapter_verse_counts":"https://quran.com/ms/surahs",
        "original_l117_withheld":True,
        "original_l117_fields_created":False,
        "matan_tajwid_expert_approved":False,
        "teacher_pbd_approved":False,
        "jawi_approved":False,
        "can_publish":False,
        "release":"NO_GO",
    }


def write(path,root=ROOT):
    r=audit(root)
    Path(path).write_text(json.dumps(r,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))


if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--output",required=True)
    args=p.parse_args();write(args.output)
