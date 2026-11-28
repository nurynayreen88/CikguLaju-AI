"""Math 5P release is explicit per PdP; ordinary private asset validation remains mandatory."""
import json
import os
from functools import lru_cache
from pathlib import Path
from web.kp2027_math_canary_web import expected_entry, FIVE_P_FLAG

MANIFEST=Path(__file__).resolve().parents[1]/"audits/rph_5p_math_kp2027_release_manifest_20261128.json"

@lru_cache(maxsize=1)
def records():
    from web.kp2027_math_5p import inventory
    _, _, drafts, reviews = inventory()
    doc=json.loads(MANIFEST.read_text(encoding="utf-8"))
    rows=doc["records"]
    expected={(g,n) for g,count in (("A",125),("B",124)) for n in range(1,count+1)}
    result={}
    for r in rows:
        g,n=r["group"],r["lesson"]
        key=g,n
        if type(n) is not int or key not in expected or key in result:
            raise ValueError("Invalid lesson identity")
        c=expected_entry(g,n)
        a=reviews[key]
        if (r["sp_code"]!=c["sp"] or r["sp_code"]!=drafts[key]["sp_code"]
            or r["source_word_sha256"]!=c["word"] or r["source_pdf_sha256"]!=c["pdf"]
            or r["dk_printed_page"]!=a["dk_printed_page"]
            or not a["source_catalog_verified"] or not a["sp_text_matched_in_combined_source"]
            or r["correction_present"] is not bool(a.get("correction"))):
            raise ValueError("Source mismatch")
        result[key]=r
    if doc["total"]!=249 or len(rows)!=249 or set(result)!=expected:
        raise ValueError("Incomplete inventory")
    return result

def released_groups(ordinary_groups=None):
    out={"A":[],"B":[]}
    if os.environ.get(FIVE_P_FLAG)!="1":
        return out
    try:
        for (g,n),r in records().items():
            if r.get("ready") is True and r.get("status")=="APPROVED_FOR_RELEASE":
                if ordinary_groups is None or n in ordinary_groups.get(g,[]):
                    out[g].append(n)
        return {g:sorted(ns) for g,ns in out.items()}
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError,AttributeError):
        return {"A":[],"B":[]}

def is_released(g,n):
    return isinstance(g,str) and type(n) is int and n in released_groups().get(g,[])
