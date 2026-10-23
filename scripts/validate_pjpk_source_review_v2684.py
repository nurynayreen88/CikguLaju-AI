"""Validate reviewed PJPK evidence packet against original queue, without writing to DB.

A reviewer must supply exact document/page and complete SK/SP evidence. No
automatic curriculum promotion occurs; accepted rows are candidates for audit.
"""
import argparse
import csv
import json
from collections import Counter
from pathlib import Path
from scripts.pjpk_source_review_packet_v2683 import FIELDS

REVIEW_STATUSES={"PENDING_SOURCE_REVIEW","SOURCE_VERIFIED","REJECTED","CONFLICT_REVIEW"}
KEY=("year_label","subject","entry_id","record_type","sp_code")
def validate(original, reviewed):
    original=list(original); reviewed=list(reviewed)
    if len(original)!=len(reviewed): raise ValueError("Review packet row count changed")
    def keys(rows):
        return Counter(tuple(r[k] for k in KEY) for r in rows)
    if keys(original)!=keys(reviewed): raise ValueError("Review packet identity mismatch")
    originals={tuple(r[k] for k in KEY):r for r in original}
    seen=set(); accepted=[]; pending=[]
    for row in reviewed:
        if set(row)!=set(FIELDS): raise ValueError("Unexpected review packet schema")
        key=tuple(row[k] for k in KEY)
        if key in seen: raise ValueError("Duplicate review identity; manual reconciliation required")
        seen.add(key)
        baseline=originals[key]
        for field in ("topic","rpt_sp_text","evidence_status","existing_dskp_text",
                      "existing_source_document","required_action"):
            if row[field]!=baseline[field]: raise ValueError("Source audit field was modified: "+field)
        status=row["review_status"]
        if status not in REVIEW_STATUSES: raise ValueError("Unknown review status")
        if status=="SOURCE_VERIFIED":
            if not all(row[k].strip() for k in ("source_document","source_page","reviewer")):
                raise ValueError("Verified source requires document, page and reviewer")
            if row["record_type"]=="SP_SOURCE_REVIEW":
                if row["reviewed_dskp_code"]!=row["sp_code"] or not row["reviewed_dskp_text"].strip():
                    raise ValueError("SP must be transcribed with exact existing code")
            elif row["record_type"]=="MISSING_SK_LINK":
                if not row["reviewed_sk_code"].strip() or not row["reviewed_sk_text"].strip():
                    raise ValueError("SK requires verified code and full source wording")
            else: raise ValueError("Unexpected record type")
            accepted.append(row)
        else:
            pending.append(row)
    return {"source_review_only":True,"production_promoted":False,"total":len(reviewed),
            "source_verified_for_further_audit":len(accepted),"still_blocked":len(pending),
            "verified":accepted}

def read_csv(path):
    with Path(path).open(encoding="utf-8-sig",newline="") as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=list(FIELDS): raise ValueError("Incorrect packet columns")
        return list(reader)
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True)
    p.add_argument("--reviewed",required=True)
    args=p.parse_args()
    print(json.dumps(validate(read_csv(args.original),read_csv(args.reviewed)),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
