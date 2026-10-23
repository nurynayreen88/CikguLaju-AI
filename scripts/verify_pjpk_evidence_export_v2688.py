"""Cross-check reviewed PJPK evidence export against the reviewed packet.

This is an audit-only integrity gate, not a DB writer or RPH release action.
"""
import argparse
import csv
import json
from collections import Counter
from scripts.validate_pjpk_source_review_v2684 import read_csv, validate
from scripts.pjpk_verified_evidence_export_v2687 import export, COLUMNS

def verify(original, reviewed, exported):
    expected=export(original,reviewed)
    if any(set(row)!=set(COLUMNS) for row in exported):
        raise ValueError("Evidence export columns changed")
    def normalized(rows):
        return Counter(tuple(str(r[k]) for k in COLUMNS) for r in rows)
    if normalized(expected)!=normalized(exported):
        raise ValueError("Evidence export does not match exact reviewed source packet")
    result=validate(original,reviewed)
    return {"audit_only":True,"production_promoted":False,
            "review_rows":result["total"],"verified_rows":len(expected),
            "blocked_rows":result["still_blocked"],"export_matches_review":True}
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--original",required=True);p.add_argument("--reviewed",required=True)
    p.add_argument("--exported",required=True);a=p.parse_args()
    with open(a.exported,encoding="utf-8",newline="") as stream:
        reader=csv.DictReader(stream)
        if reader.fieldnames!=list(COLUMNS):raise ValueError("Invalid evidence export header")
        exported=list(reader)
    print(json.dumps(verify(read_csv(a.original),read_csv(a.reviewed),exported),
                     ensure_ascii=False,indent=2))
if __name__=="__main__":main()
