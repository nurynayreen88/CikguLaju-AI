"""Produce a source-review packet for all PJPK T1–T6 gaps, without guessing SK/SP."""
import argparse
import csv
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from scripts.pjpk_source_gap_queue_v2679 import build_queue

FIELDS=("year_label","subject","entry_id","topic","record_type","sp_code","rpt_sp_text",
        "evidence_status","existing_dskp_text","existing_source_document","required_action",
        "reviewed_dskp_code","reviewed_dskp_text","reviewed_sk_code","reviewed_sk_text",
        "source_document","source_page","reviewer","review_status","review_notes")
def packet(rows):
    output=[]
    for r in rows:
        if r["record_type"] not in ("SP_SOURCE_REVIEW","MISSING_SK_LINK"):
            raise ValueError("Unknown review record type")
        output.append(dict(zip(FIELDS,(
            r["year"],r["subject"],r["entry_id"],r["topic"],r["record_type"],
            r["standard_code"],r["rpt_text"],r["evidence_status"],
            r["direct_dskp_text"],r["source_document"],r["action"],
            "","","","","","","","PENDING_SOURCE_REVIEW",""))))
    if len(output)!=len(rows): raise ValueError("Review packet lost rows")
    return output

def main():
    p=argparse.ArgumentParser()
    p.add_argument("--db",required=True)
    p.add_argument("--output",required=True)
    args=p.parse_args()
    rows=packet(build_queue(args.db))
    dest=Path(args.output)
    dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open("w",encoding="utf-8-sig",newline="") as stream:
        writer=csv.DictWriter(stream,fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    print(json.dumps({"review_rows":len(rows),"output":str(dest),
                      "production_promoted":False,"read_only_source":True}))

if __name__=="__main__":main()
