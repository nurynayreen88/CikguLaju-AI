"""Prevent source-SP surah / RPH objective / PBD verse crosswiring.

The educational source RPT2027 itself carried some wrong copy/pasted surah
names. This verifier checks the corrected *staging RPH*, preserves original
field text in source-correction metadata, and refuses publication approval.
It does NOT prove that the DSKP/Jawi wording is academically certified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re

from pi_quality_audit import COUNT, HELD, ROOT

# Sura names observed in original curriculum RPT / RPH sources. A word after
# 'سورة' isn't automatically a surah: it can be 'tersebut', 'dalam', etc.
SURAH_NAMES = set("""ابراهيم الأحزاب الأعراف الأعلى الأنبياء الأنعام الأنفال
الإخلاص الإسراء الإنفطار البقرة التكاثر التكوير التوبة التين الحج الحجر
الرعد الروم الزمر السجدة الشرح الشعراء الصاڤات الضحى الطارق الطور العصر
العنكبوت الغاشية الفاتحة الفجر الفرقان الفلق القارعة القدر القصص القمر
الكافرون الكهف المؤمنون المائدة الماعون المطففين الناس النحل النساء
النمل النور سباء ص طه عبس غافر فاطر فصلت لقمان مريم هود يس يونس""".split())
NAMES_PATTERN=re.compile(r"سورة\s+([ء-ۿ]+)")
RANGE_PATTERN=re.compile(r"سورة\s+([ء-ۿ]+)\s+(?:أية|اية|آية)\s*(\d{1,3})\s*[-–]\s*(\d{1,3})")
CHANGED={
  "T3-L011":("aktiviti_utama",),
  "T3-L023":("aktiviti_utama",),
  "T3-L086":("objektif",),
  "T3-L089":("set_induksi",),
  "T3-L093":("set_induksi",),
  "T4-L009":("set_induksi","pentaksiran"),
  "T4-L013":("set_induksi","pentaksiran"),
  "T4-L081":("set_induksi",),
  "T4-L085":("set_induksi","pentaksiran"),
  "T4-L093":("pentaksiran",),
  "T5-L069":("set_induksi",),
}
RPT_SOURCE_ERRORS=set(("T3-L086","T3-L089","T3-L093","T4-L009",
                       "T4-L013","T4-L081","T4-L085"))

def normalize(s):
    s=re.sub(r"[\u064b-\u065f\u0670\u0640]","",s)
    return s.replace("ٱ","ا").replace("آ","ا").replace("أ","ا").replace("إ","ا").replace("ى","ي")


def named_surahs(s):
    valid={normalize(s) for s in SURAH_NAMES}
    return set(normalize(m.group(1)) for m in NAMES_PATTERN.finditer(s)
               if normalize(m.group(1)) in valid)


def ranges(s):
    valid={normalize(x) for x in SURAH_NAMES}
    return {(normalize(name),int(first),int(last))
            for name,first,last in RANGE_PATTERN.findall(s)
            if normalize(name) in valid}


def audit(root=ROOT):
    allrows=[]
    for year,num in COUNT.items():
        source=json.loads((Path(root)/f"year{year}.json").read_text(encoding="utf-8"))
        assert source["year"]==year and source["ready"] is False
        assert len(source["records"])==num
        allrows+=source["records"]
    assert len(allrows)==696
    problems=[]
    validated=0
    result=[]
    for row in allrows:
        if row["withheld"]:
            assert (row["tahun"],row["lesson"]) in HELD
            continue
        f=row["fields"]
        expected=named_surahs(f["sp"])
        if expected:
            validated+=1
            for field in ("objektif","set_induksi","aktiviti_utama","pentaksiran"):
                off_topic=sorted(named_surahs(f[field])-expected)
                if off_topic:
                    problems.append({"id":row["id"],"field":field,
                                     "surah_not_in_source_sp":off_topic})
            objectives=ranges(f["objektif"])
            for pbd_range in ranges(f["pentaksiran"]):
                if objectives and pbd_range not in objectives:
                    problems.append({"id":row["id"],"field":"pentaksiran",
                                     "pbd_verse_range_not_in_objective":pbd_range})
        if row["id"] in CHANGED:
            meta=row["staging_cross_field_source_correction"]
            assert meta["revision"]=="pi-surah-pbd-20261108"
            assert set(meta["original_fields"])==set(meta["revised_fields"])==set(CHANGED[row["id"]])
            assert all(meta["original_fields"][key]!=meta["revised_fields"][key]
                       and f[key]==meta["revised_fields"][key]
                       for key in CHANGED[row["id"]])
            assert meta["sk_sp_unchanged"] is True
            assert meta["source_rpt_has_copy_error"]==(row["id"] in RPT_SOURCE_ERRORS)
            assert meta["content_expert_approved"] is False
            assert meta["jawi_orthography_approved"] is False
            assert meta["publication"]=="HOLD"
            assert row["verified_ready"] is False
            result.append({"id":row["id"],"repaired_fields":CHANGED[row["id"]],
                           "RPT_source_copy_error":row["id"] in RPT_SOURCE_ERRORS,
                           "source_sp_unmodified":True,"teacher_ready":False})
    assert len(result)==len(CHANGED)==11
    assert not problems,problems[:10]
    assert validated>=180
    return {
       "scope":"PI YEAR2-6 696; isolated source-SP alignment review only",
       "quran_rph_with_explicit_source_surah_checked":validated,
       "named_surah_or_pbd_range_remaining_mismatches":len(problems),
       "lessons_with_precise_corrections":len(result),
       "curriculum_RPT2027_copy_errors_flagged":len(RPT_SOURCE_ERRORS),
       "generic_activity_steps_replaced":2,
       "original_fields_preserved_in_metadata":True,
       "source_RPT2027_modified":False,
       "source_DSKP_modified":False,
       "expert_Quran_validation_approved":0,
       "teacher_publishable":0,
       "academic_quality_percent":None,
       "release":"NO_GO",
       "rows":result,
       "problems":problems
    }


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--output",required=True)
    args=ap.parse_args()
    result=audit()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",
                                 encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("rows","problems")},
                     ensure_ascii=False,indent=2))
