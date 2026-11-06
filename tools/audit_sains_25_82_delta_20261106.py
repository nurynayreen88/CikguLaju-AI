"""Diff v25.68 vs v25.82 science records: read-only, never upgrade implicitly."""
from __future__ import annotations
import json
import sqlite3
import tempfile
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SOURCES={
    "v25.68":"CikguLaju_Curriculum_Master_v25_68_SCIENCE_MATH_UPLOAD_READY.db",
    "v25.82":"CikguLaju_Curriculum_Master_v25_82_PRIMARY_LANGUAGE_SCIENCE_VERB_QA.db",
}
def load(name,base,temp):
    parts=sorted(base.glob(name+".part*"))
    if not parts:
        raise RuntimeError("Source missing: "+name)
    target=temp/(name+".readonly.db")
    with target.open("wb") as dst:
        for p in parts:
            with p.open("rb") as src:
                for ch in iter(lambda:src.read(1024*1024),b""):
                    dst.write(ch)
    with sqlite3.connect(target.resolve().as_uri()+"?mode=ro&immutable=1",uri=True) as db:
        db.row_factory=sqlite3.Row
        if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
            raise RuntimeError("Source integrity failed "+name)
        return [dict(r) for r in db.execute(
            "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")]
def diff():
    with tempfile.TemporaryDirectory(prefix="sains_68_82_cmp_") as tmp:
        a=load(SOURCES["v25.68"],ROOT,Path(tmp))
        b=load(SOURCES["v25.82"],ROOT,Path(tmp))
    k=lambda r:(r.get("year_label"),r.get("pdp_sequence_code"))
    left={k(r):r for r in a}
    right={k(r):r for r in b}
    common=set(left)&set(right)
    changed=[]
    for key in sorted(common):
        before,after=left[key],right[key]
        cols=set(before)|set(after)
        delta={c:{"v25_68":before.get(c),"v25_82":after.get(c)}
               for c in cols if before.get(c)!=after.get(c)}
        if delta:
            changed.append({"year":key[0],"pdp_code":key[1],"changes":delta})
    return {
        "status":"AUDIT_ONLY_NOT_RELEASE",
        "v25_68_rows":len(a),
        "v25_82_rows":len(b),
        "unchanged_codes":len(common)-len(changed),
        "added_codes":len(set(right)-set(left)),
        "removed_codes":len(set(left)-set(right)),
        "changes_count":len(changed),
        "changed_field_counts":dict(Counter(c for x in changed for c in x["changes"])),
        "changed_rows_sample":changed[:35],
        "y3_5_original_codes":{code:{
            "v25_68_title":left.get(("Tahun 3",code),{}).get("pdp_title"),
            "v25_82_title":right.get(("Tahun 3",code),{}).get("pdp_title"),
        } for code in ("SCI-Y3-PDP-002","SCI-Y3-PDP-005",
                       "SCI-Y3-PDP-011","SCI-Y3-PDP-020","SCI-Y3-PDP-021")},
        "note":"Only compare; do not overwrite or conflate source checks with user RPH readiness."
    }
if __name__=="__main__":
    print(json.dumps(diff(),ensure_ascii=False,indent=2))
