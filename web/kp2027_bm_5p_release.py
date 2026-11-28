"""Per-lesson BM KP2027 release gate; initial review is not approval."""
from functools import lru_cache
import json
import os
from pathlib import Path
from web import kp2027_bm_rpt_aligned as bm

REVIEW = Path(__file__).resolve().parents[1] / "audits/rph_5p_bm_kp2027_batch01_content_release_review_20261128.json"
FLAG = "CIKGULAJU_BM_KP2027_5P_ENABLED"
PHASES = {"engagement", "exploration", "explanation", "elaboration", "evaluation"}

@lru_cache(maxsize=1)
def reviewed_records():
    from web.kp2027_bm_5p import companions
    data = json.loads(REVIEW.read_text(encoding="utf-8"))
    rows = data["records"]
    if len(rows) != 24 or data.get("total") != 24:
        raise bm.Unavailable("Inventori semakan 5P tidak sah")
    result = {}
    for row in rows:
        g, n = row["group"], row["lesson"]
        r = bm.lesson(g, n)
        key = (g, n)
        phases = row["proposed_phases"]
        if (key in result or type(n) is not int
            or row["sp_code"] != r["sp_code"]
            or row["source_sp"] != r["sp"]
            or row["source_criteria"] != r["criteria"]
            or row["source_objective"] != r["objective"]
            or row["source_material"] != r["material"]
            or row["original_phases"] != companions()[key]
            or set(phases) != PHASES
            or not all(isinstance(x, str) and x.strip() for x in phases.values())
            or len(set(phases.values())) != 5):
            raise bm.Unavailable("Padanan sumber semakan 5P tidak sah")
        result[key] = row
    if set(result) != {(g,n) for g in ("A","B") for n in range(1,13)}:
        raise bm.Unavailable("Senarai semakan 5P tidak lengkap")
    return result

def released_groups():
    result = {"A": [], "B": []}
    if os.environ.get(FLAG) != "1":
        return result
    try:
        rows = reviewed_records()
        for (g,n), row in rows.items():
            if row.get("ready") is True and row.get("status") == "APPROVED_FOR_RELEASE":
                result[g].append(n)
        return {g: sorted(ns) for g,ns in result.items()}
    except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError):
        return {"A": [], "B": []}

def is_released(g,n):
    return type(n) is int and isinstance(g,str) and n in released_groups().get(g, [])

def reviewed_phases(g,n):
    return dict(reviewed_records()[g,n]["proposed_phases"])
