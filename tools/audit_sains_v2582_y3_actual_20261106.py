"""Year3 v25.82 *actual* latest shipped sequence inventory, read-only.

Does NOT assume 25.68 code identities survive, even when code string same.
"""
import json
import tempfile
from pathlib import Path
from collections import Counter
from tools.audit_sains_25_82_delta_20261106 import load, SOURCES, ROOT

def inspect():
    with tempfile.TemporaryDirectory(prefix="sains_latest_2582_") as tmp:
        rows=load(SOURCES["v25.82"],ROOT,Path(tmp))
    y3=sorted((r for r in rows if r.get("year_label")=="Tahun 3"),
              key=lambda r:int(r.get("source_sequence_no") or 9999))
    codes=[str(r.get("sp_code") or "").strip() for r in y3]
    return {
        "source":"v25.82 historical shipped, NOT proven active at Render",
        "release_decision":"HOLD",
        "year3_count":len(y3),
        "year3_sp_distinct":len(set(codes)),
        "year3_status_counts":dict(Counter(r.get("verification_status") for r in y3)),
        "year3_missing_sp":sum(not r.get("sp_code") for r in y3),
        "year3_missing_textbook_ref":sum(not r.get("textbook_ref") for r in y3),
        "year3_sequence_numbers":[r.get("source_sequence_no") for r in y3],
        "year3_pdp": [{
            "code":r.get("pdp_sequence_code"),
            "order":r.get("source_sequence_no"),
            "unit":r.get("unit_title"),
            "sk":r.get("sk_code"),
            "sp":r.get("sp_code"),
            "title":r.get("pdp_title"),
            "status":r.get("verification_status"),
        } for r in y3]
    }

if __name__=="__main__":
    print(json.dumps(inspect(),ensure_ascii=False,indent=2))
