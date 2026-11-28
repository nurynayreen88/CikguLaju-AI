"""Per-lesson Science 5P publication gate, separate from the QA candidate.
No production blueprint registration or permission to render teaching copies here.
"""
import json
import os
from functools import lru_cache
from pathlib import Path
from tools.audit_science_native_5p_documents_20261128 import inventory, support_inventory, git_blob

ROOT=Path(__file__).resolve().parents[1]
MANIFEST=ROOT/"audits/rph_5p_science_y5_y6_release_manifest_20261128.json"
FLAG="CIKGULAJU_SCIENCE_5P_ENABLED"
COUNTS={5:116,6:89}

@lru_cache(maxsize=1)
def records():
    d=json.loads(MANIFEST.read_text(encoding="utf-8"))
    expected_paths={f"audits/rph_5p_science_y{y}_{part}_20261128.json"
        for y in COUNTS for part in ("native_complete_identity_audit","pedagogical_review_complete",
                                       "print_corrections","support_complete_audit")}
    if set(d["source_blobs"])!=expected_paths:
        raise ValueError("Science release evidence incomplete")
    for p,digest in d["source_blobs"].items():
        if git_blob((ROOT/p).read_bytes())!=digest:
            raise ValueError("Science release source changed")
    expected={}
    for y in COUNTS:
        rows=inventory(y)
        support_inventory(y,rows)
        corrections=json.loads((ROOT/f"audits/rph_5p_science_y{y}_print_corrections_20261128.json").read_text(encoding="utf-8"))
        corrected={r["lesson_id"] for r in corrections["records"]}
        if corrections["held"]:
            raise ValueError("Held Science corrections")
        for r in rows:
            expected[y,r["lesson_id"]]={
                "unit":r["unit"],"title":r["title"],
                "sp_codes":[r["sp_code"]] if y==5 else [sp["code"] for sp in r["sp"]],
                "textbook_pages":r["textbook_pages"],"minutes":r["minutes"],
                "correction_present":r["lesson_id"] in corrected}
    out={}
    for r in d["records"]:
        key=(r["year"],r["lesson_id"])
        if type(r["year"]) is not int or key not in expected or key in out:
            raise ValueError("Science release identity mismatch")
        if any(r.get(k)!=v for k,v in expected[key].items()):
            raise ValueError("Science release content mismatch")
        if type(r.get("ready")) is not bool:
            raise ValueError("Science approval marker invalid")
        out[key]=r
    if d["total"]!=205 or len(d["records"])!=205 or set(out)!=set(expected):
        raise ValueError("Science release catalogue incomplete")
    if sum(r["correction_present"] for r in out.values())!=82:
        raise ValueError("Science correction inventory incomplete")
    return out

def is_released(year, lesson):
    if os.getenv(FLAG)!="1" or type(year) is not int or not isinstance(lesson,str):
        return False
    try:
        r=records().get((year,lesson),{})
        return r.get("ready") is True and r.get("status")=="APPROVED_FOR_RELEASE"
    except (OSError,ValueError,TypeError,KeyError,RuntimeError,ImportError,AttributeError):
        return False
