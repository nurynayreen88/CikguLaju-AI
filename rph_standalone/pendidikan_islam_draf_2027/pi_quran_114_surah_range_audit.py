"""Independent whole-catalog check: Quran chapter names and printed verse ranges.

Source: Quran.com Surah List, https://quran.com/surahs (114 chapters, 6236 ayat).
These are chapter lengths, NOT approval of lesson's Juz selection or SP code.
The original 2027 RPT/DSKP is kept unchanged; academic approval still HOLD.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
import unicodedata

from pi_quality_audit import COUNT, HELD, ROOT

# Hafs/Kufan chapter counts, from the full Quran.com chapter listing.
# The count sum and number of chapter entries are both asserted below.
QURAN_114 = """الفاتحة:7 البقرة:286 آل_عمران:200 النساء:176 المائدة:120 الأنعام:165 الأعراف:206 الأنفال:75 التوبة:129 يونس:109 هود:123 يوسف:111 الرعد:43 ابراهيم:52 الحجر:99 النحل:128 الإسراء:111 الكهف:110 مريم:98 طه:135 الأنبياء:112 الحج:78 المؤمنون:118 النور:64 الفرقان:77 الشعراء:227 النمل:93 القصص:88 العنكبوت:69 الروم:60 لقمان:34 السجدة:30 الأحزاب:73 سبأ:54 فاطر:45 يس:83 الصافات:182 ص:88 الزمر:75 غافر:85 فصلت:54 الشورى:53 الزخرف:89 الدخان:59 الجاثية:37 الأحقاف:35 محمد:38 الفتح:29 الحجرات:18 ق:45 الذاريات:60 الطور:49 النجم:62 القمر:55 الرحمن:78 الواقعة:96 الحديد:29 المجادلة:22 الحشر:24 الممتحنة:13 الصف:14 الجمعة:11 المنافقون:11 التغابن:18 الطلاق:12 التحريم:12 الملك:30 القلم:52 الحاقة:52 المعارج:44 نوح:28 الجن:28 المزمل:20 المدثر:56 القيامة:40 الإنسان:31 المرسلات:50 النبأ:40 النازعات:46 عبس:42 التكوير:29 الإنفطار:19 المطففين:36 الإنشقاق:25 البروج:22 الطارق:17 الأعلى:19 الغاشية:26 الفجر:30 البلد:20 الشمس:15 الليل:21 الضحى:11 الشرح:8 التين:8 العلق:19 القدر:5 البينة:8 الزلزلة:8 العاديات:11 القارعة:11 التكاثر:8 العصر:3 الهمزة:9 الفيل:5 قريش:4 الماعون:7 الكوثر:3 الكافرون:6 النصر:3 المسد:5 الإخلاص:4 الفلق:5 الناس:6"""

def normal(text):
    text=unicodedata.normalize("NFKC",text)
    text=re.sub(r"[\u064b-\u065f\u0670\u0640]","",text)
    return text.translate(str.maketrans("آأإٱى","ااااي"))

def verse_catalog():
    pairs=[token.split(":") for token in QURAN_114.split()]
    assert len(pairs)==114
    assert sum(int(count) for name,count in pairs)==6236
    catalog={normal(name.replace("_"," ")):int(count) for name,count in pairs}
    assert len(catalog)==114
    aliases={
        "النباء":"النبأ", # some source RPTs spell an-Naba' as النباء
        "الصاڤات":"الصافات", # RPT Jawi non-Arabic PEH variant
        "الانفطار":"الإنفطار",
        "سباء":"سبأ", # RPT Year5 Jawi form with hamzah on line
        "الاحقاڤ":"الأحقاف", # Year6 Jawi PEH spelling of al-Ahqaf
    }
    for alias,primary in aliases.items():
        catalog[normal(alias)]=catalog[normal(primary)]
    return catalog

CATALOG=verse_catalog()
NAMES=sorted(CATALOG,key=len,reverse=True)
RANGE_PATTERN=re.compile(
    r"(?<![\u0621-\u06FF])("
    + "|".join(map(re.escape,NAMES))
    + r")\s*(?:(?:اية|ايات|ءاية)\s*)?(\d{1,3})\s*[-–]\s*(\d{1,3})(?!\d)"
)
CHECK_FIELDS=("sp","objektif","aktiviti_utama","pentaksiran")
REPAIRS={
    "T3-L001":{"objektif","aktiviti_utama"},
    "T3-L005":{"objektif","aktiviti_utama"},
    "T5-L034":{"sp","objektif","aktiviti_utama"},
    "T6-L078":{"objektif"}
}

def parse(text):
    return [
        {"surah":m.group(1),"start":int(m.group(2)),
         "end":int(m.group(3)),"surah_total_ayat":CATALOG[m.group(1)]}
        for m in RANGE_PATTERN.finditer(normal(text))
    ]

def to_tuple(x):
    return (x["surah"],x["start"],x["end"])

def audit(root=ROOT):
    rows=[]
    parsed_counter=Counter()
    nonempty={"sp":0,"objektif":0,"aktiviti_utama":0,"pentaksiran":0}
    invalid=[]
    crossfield=[]
    corrected=[]
    for year,expected in COUNT.items():
        data=json.loads((Path(root)/f"year{year}.json").read_text(encoding="utf-8"))
        assert data["year"]==year and data["ready"] is False
        assert len(data["records"])==expected
        for r in data["records"]:
            if r["withheld"]:
                assert (year,r["lesson"]) in HELD and "fields" not in r
                continue
            assert r["verified_ready"] is False
            spans={field:parse(r["fields"][field]) for field in CHECK_FIELDS}
            for field,values in spans.items():
                parsed_counter[field]+=len(values)
                if values:nonempty[field]+=1
                for item in values:
                    if item["start"]<1 or item["start"]>item["end"] or item["end"]>item["surah_total_ayat"]:
                        invalid.append({"id":r["id"],"field":field,**item})
            if spans["sp"] and spans["objektif"]:
                forbidden={to_tuple(x) for x in spans["objektif"]}-{to_tuple(x) for x in spans["sp"]}
                if forbidden:
                    crossfield.append({"id":r["id"],"type":"objective_does_not_match_SP",
                                      "ranges":sorted(forbidden)})
            for field in ("aktiviti_utama","pentaksiran"):
                if spans["objektif"] and spans[field]:
                    forbidden={to_tuple(x) for x in spans[field]}-{to_tuple(x) for x in spans["objektif"]}
                    if forbidden:
                        crossfield.append({"id":r["id"],"type":field+"_ranges_differ_from_objective",
                                           "ranges":sorted(forbidden)})
            if r["id"] in REPAIRS:
                meta=r["staging_quran_name_range_primary_source_correction"]
                assert meta["revision"]=="pi-surah-normalization-verse-order-20261108"
                assert set(meta["original_fields"])==set(meta["revised_fields"])==REPAIRS[r["id"]]
                assert all(meta["revised_fields"][f]==r["fields"][f] and
                           meta["original_fields"][f]!=r["fields"][f] for f in REPAIRS[r["id"]])
                assert meta["publication"]=="HOLD" and meta["specialist_tajwid_jawi_approved"] is False
                corrected.append(r["id"])
            rows.append({"id":r["id"],"year":year,
                         "source_sp_ranges":len(spans["sp"]),
                         "objective_ranges":len(spans["objektif"]),
                         "activity_ranges":len(spans["aktiviti_utama"]),
                         "pbd_ranges":len(spans["pentaksiran"]),
                         "lesson_release":"NO_GO"})
    assert len(rows)==690
    assert len(corrected)==4
    assert not invalid,invalid[:10]
    assert not crossfield,crossfield[:10]
    assert sum(parsed_counter.values())>=750,parsed_counter
    return {
        "catalog_lesson_total":696,
        "unheld_drafts_examined":len(rows),
        "source":"https://quran.com/surahs",
        "quran_chapter_total":114,"quran_verse_total":6236,
        "verse_range_occurrences_evaluated":sum(parsed_counter.values()),
        "verse_range_occurrences_by_field":dict(parsed_counter),
        "RPH_corrected_after_rechecking":sorted(corrected),
        "invalid_chapter_verse_ranges":len(invalid),
        "crossfield_surah_verse_mismatches":len(crossfield),
        "unparseable_source_verse_ranges_are_not_certified":True,
        "original_rpt_overwritten":False,
        "specialist_approved":0,"teacher_ready":0,
        "release":"NO_GO","rows":rows,"invalid":invalid,"crossfield":crossfield
    }

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--output",required=True)
    args=p.parse_args()
    result=audit()
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:v for k,v in result.items() if k not in ("rows","invalid","crossfield")},
                     ensure_ascii=False,indent=2))
