"""Strictly reconcile a reviewed PJPK packet against exact-scope original rows.

Only produces an audit manifest. Does not change the candidate or production DB.
"""
import argparse
import json
from collections import Counter
from pathlib import Path
from scripts.validate_pjpk_source_review_v2684 import read_csv,validate

def manifest(original, reviewed):
    result=validate(original,reviewed)
    scopes={}
    for r in reviewed:
        key=(r["year_label"],r["subject"])
        scope=scopes.setdefault(key,{"year":key[0],"subject":key[1],
            "review_rows":0,"verified_for_further_audit":0,"blocked":0})
        scope["review_rows"]+=1
        if r["review_status"]=="SOURCE_VERIFIED":scope["verified_for_further_audit"]+=1
        else:scope["blocked"]+=1
    ordered=[scopes.get((f"Tahun {y}",s),{"year":f"Tahun {y}","subject":s,
        "review_rows":0,"verified_for_further_audit":0,"blocked":0})
        for y in range(1,7) for s in ("Pendidikan Jasmani","Pendidikan Kesihatan")]
    if sum(s["review_rows"] for s in ordered)!=result["total"]:raise ValueError("Scope count mismatch")
    if sum(s["blocked"] for s in ordered)!=result["still_blocked"]:raise ValueError("Blocked count mismatch")
    if sum(s["verified_for_further_audit"] for s in ordered)!=result["source_verified_for_further_audit"]:
        raise ValueError("Verified count mismatch")
    return {"scope_count":12,"source_review_only":True,"production_promoted":False,
        "total":result["total"],"still_blocked":result["still_blocked"],
        "verified_for_further_audit":result["source_verified_for_further_audit"],"scopes":ordered}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True);p.add_argument("--reviewed",required=True)
    args=p.parse_args()
    print(json.dumps(manifest(read_csv(args.original),read_csv(args.reviewed)),ensure_ascii=False,indent=2))
if __name__=="__main__":main()
