"""Determine 12 curriculum-topic clusters for 29 Sains SP not in 342 source PdP.

Read-only: proposed integration into existing SK topic, or genuinely absent SK
requiring a new unit planning decision. Never manufacture 2027 RPH or dates.
"""
from __future__ import annotations
from pathlib import Path
from collections import defaultdict
import json

from scripts.audit_sains_rpt2027_uncovered_verified_sp_staging import audit_coverage, ROOT
from scripts.build_rpt_2027_sains_342_actual_source_staging import source_records

OUT=ROOT/"staging/rpt_2027_seragam_2026/sains_29_sp_12_topic_clusters_review_20261107_DRAF.json"

def group_29_content_sp():
    audit=audit_coverage()
    original=source_records()
    result=[]
    expected={4:6,5:2,6:4}
    for year in (4,5,6):
        source=original[year]
        bysk=defaultdict(list)
        for row in source:
            bysk[row["sk"]].append({"pdp_id":row["id"],"title":row["topic"],"sp":row["sp"],"unit":row["unit"]})
        clusters=defaultdict(list)
        for std in audit["years"][str(year)]["subject_content_requires_textbook_rph_reconciliation"]:
            clusters[std["sk_code"]].append(std)
        if len(clusters)!=expected[year]:
            raise ValueError(f"Y{year} expected {expected[year]} distinct missing topic clusters; got {len(clusters)}")
        for sk,items in sorted(clusters.items(),key=lambda x:tuple(map(int,x[0].split(".")))):
            titles={x["sk_text"] for x in items}
            if len(titles)!=1:
                raise ValueError("Contradictory verified SK titles across missing SP")
            nearby=bysk.get(sk,[])
            result.append({
                "year":year,"sk_code":sk,"sk_statement":next(iter(titles)),
                "missing_content_sp_count":len(items),
                "missing_sp":[{"sp_code":x["sp_code"],"sp_statement":x["sp_text"],"source":x["source"]} for x in items],
                "existing_historical_pdp_same_sk":nearby,
                "candidate_action":("ATTACH_WITH_EXPLICIT_ACTIVITY_RPH_REVIEW" if nearby
                                    else "NEW_TOPIC_UNIT_NEEDS_TEXTBOOK_SOURCE_AND_LESSON_PLAN"),
                "proposed_lesson_week":None,"approved_for_release":False,
            })
    if len(result)!=12 or sum(c["missing_content_sp_count"] for c in result)!=29:
        raise ValueError("29 content SP must form exact 12 SK-based topic clusters")
    if len({(c["year"],x["sp_code"]) for c in result for x in c["missing_sp"]})!=29:
        raise ValueError("Duplicate or missing Sains SP")
    return {
        "date":"2026-11-07",
        "status":"STAGING_12_SOURCE_SK_TOPIC_CLUSTERS_NOT_LESSON_APPROVAL",
        "year_counts":{str(y):sum(c["year"]==y for c in result) for y in (4,5,6)},
        "topic_clusters":len(result),"unrepresented_content_sp":29,
        "counts_are_not_new_lessons":True,"production_changes":0,
        "clusters":result,
    }

def write_report(out=OUT):
    info=group_29_content_sp()
    dest=Path(out);dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(info,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return dest

if __name__=="__main__":
    result=write_report()
    doc=json.loads(result.read_text(encoding="utf-8"))
    for item in doc["clusters"]:
        print(item["year"],"SK",item["sk_code"],"SP missing",item["missing_content_sp_count"],"existing PdP",len(item["existing_historical_pdp_same_sk"]),item["candidate_action"])
    print("Sains 12 cluster review:",result)
