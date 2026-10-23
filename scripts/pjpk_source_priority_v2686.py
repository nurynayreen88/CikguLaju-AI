"""Prioritize PJPK source-review packet by evidence work, preserving all 12 scopes."""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from scripts.validate_pjpk_source_review_v2684 import read_csv
from scripts.pjpk_source_review_packet_v2683 import FIELDS

def plan(rows):
    rows=list(rows)
    scopes=[]
    for year in (f"Tahun {n}" for n in range(1,7)):
        for subject in ("Pendidikan Jasmani","Pendidikan Kesihatan"):
            scoped=[r for r in rows if (r["year_label"],r["subject"])==(year,subject)]
            by_entry={}
            for r in scoped:
                if r["record_type"] not in ("SP_SOURCE_REVIEW","MISSING_SK_LINK"):
                    raise ValueError("Unknown review type")
                if r["review_status"] not in ("PENDING_SOURCE_REVIEW","SOURCE_VERIFIED","REJECTED","CONFLICT_REVIEW"):
                    raise ValueError("Unknown review status")
                by_entry.setdefault(r["entry_id"],[]).append(r)
            work=[]
            for entry,items in by_entry.items():
                pending=[r for r in items if r["review_status"]!="SOURCE_VERIFIED"]
                work.append({"entry_id":entry,"topic":items[0]["topic"],"review_rows":len(items),
                    "pending":len(pending),"sp_reviews":sum(r["record_type"]=="SP_SOURCE_REVIEW" for r in pending),
                    "missing_sk":sum(r["record_type"]=="MISSING_SK_LINK" for r in pending),
                    "conflicts":sum(r["evidence_status"]=="CONFLICT_REVIEW" for r in pending)})
            work.sort(key=lambda w:(-w["conflicts"],-w["missing_sk"],-w["sp_reviews"],str(w["entry_id"])))
            scopes.append({"year":year,"subject":subject,"review_rows":len(scoped),
                "unique_entries":len(work),"pending":sum(w["pending"] for w in work),"work":work})
    if sum(s["review_rows"] for s in scopes)!=len(rows):raise ValueError("Rows lost in prioritization")
    return {"scope_count":12,"review_rows":len(rows),"read_only":True,
            "production_promoted":False,"scopes":scopes}
def main():
    p=argparse.ArgumentParser();p.add_argument("--packet",required=True);a=p.parse_args()
    print(json.dumps(plan(read_csv(a.packet)),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
