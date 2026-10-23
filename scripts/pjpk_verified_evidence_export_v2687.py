"""Export source-verified PJPK evidence only, never automatically release curriculum."""
import argparse
import csv
import json
import sys
from scripts.validate_pjpk_source_review_v2684 import read_csv,validate

COLUMNS=("year_label","subject","entry_id","record_type","sp_code",
         "reviewed_dskp_code","reviewed_dskp_text","reviewed_sk_code",
         "reviewed_sk_text","source_document","source_page","reviewer")
def export(original,reviewed):
    result=validate(original,reviewed)
    accepted=result["verified"]
    conflicts={}
    for row in accepted:
        code=row["reviewed_dskp_code"] if row["record_type"]=="SP_SOURCE_REVIEW" else row["reviewed_sk_code"]
        wording=row["reviewed_dskp_text"] if row["record_type"]=="SP_SOURCE_REVIEW" else row["reviewed_sk_text"]
        key=(row["year_label"],row["subject"],row["record_type"],code)
        if key in conflicts and conflicts[key]!=wording.strip():
            raise ValueError("Contradictory reviewed source wording for exact curriculum scope")
        conflicts[key]=wording.strip()
    return [{key:row[key] for key in COLUMNS} for row in accepted]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True);p.add_argument("--reviewed",required=True)
    p.add_argument("--output",required=True)
    a=p.parse_args()
    rows=export(read_csv(a.original),read_csv(a.reviewed))
    with open(a.output,"w",encoding="utf-8",newline="") as f:
        writer=csv.DictWriter(f,fieldnames=COLUMNS);writer.writeheader();writer.writerows(rows)
    print(json.dumps({"source_verified_rows":len(rows),"production_promoted":False,
                      "output":a.output},ensure_ascii=False),file=sys.stderr)
if __name__=="__main__":main()
