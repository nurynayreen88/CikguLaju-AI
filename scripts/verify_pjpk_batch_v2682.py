"""Independent cross-check for PJPK 12-scope queue, summary and entry worklist."""
import json
import sys
from pathlib import Path

def verify(queue_data, summary, worklist):
    rows=queue_data["items"]
    if queue_data["queue_count"] != len(rows): raise ValueError("Queue count mismatch")
    if any(obj["production_promoted"] is not False or obj["read_only"] is not True
           for obj in (queue_data,summary,worklist)): raise ValueError("Unsafe release flags")
    if summary["scope_count"] != 12 or worklist["scope_count"] != 12: raise ValueError("Missing scopes")
    if summary["review_rows"] != len(rows) or worklist["review_rows"] != len(rows): raise ValueError("Review totals differ")
    source_keys = [(r["year"],r["subject"],r["entry_id"],r["record_type"],
                    r["standard_code"] if r["record_type"]=="SP_SOURCE_REVIEW" else "") for r in rows]
    output_keys=[]
    for scope in worklist["scopes"]:
        if scope["unique_entries"] != len(scope["entries"]): raise ValueError("Entry count mismatch")
        if scope["review_rows"] != sum(len(e["sp_reviews"])+int(e["missing_sk_link"]) for e in scope["entries"]):
            raise ValueError("Scope review mismatch")
        for entry in scope["entries"]:
            if (entry["year"],entry["subject"]) != (scope["year"],scope["subject"]): raise ValueError("Scope leakage")
            for sp in entry["sp_reviews"]:
                output_keys.append((entry["year"],entry["subject"],entry["entry_id"],"SP_SOURCE_REVIEW",sp["code"]))
            if entry["missing_sk_link"]:
                output_keys.append((entry["year"],entry["subject"],entry["entry_id"],"MISSING_SK_LINK",""))
    from collections import Counter
    if Counter(source_keys)!=Counter(output_keys): raise ValueError("Worklist lost or duplicated source reviews")
    if sum(s["unique_entries"] for s in worklist["scopes"])!=worklist["unique_entries"]:
        raise ValueError("Unique entry total mismatch")
    if sum(s["review_rows"] for s in summary["scopes"])!=len(rows): raise ValueError("Summary scope totals mismatch")
    return {"validated":True,"review_rows":len(rows),"unique_entries":worklist["unique_entries"],"scopes":12,
            "production_promoted":False}

def main():
    if len(sys.argv)!=4: raise SystemExit("usage: verify queue.json summary.json worklist.json")
    data=[json.loads(Path(p).read_text(encoding="utf-8")) for p in sys.argv[1:]]
    print(json.dumps(verify(*data),ensure_ascii=False,indent=2))

if __name__=="__main__":main()
