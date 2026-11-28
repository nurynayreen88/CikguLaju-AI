"""Per-lesson BM KP2027 release gate; initial review is not approval."""
from functools import lru_cache
import json
import os
from pathlib import Path
from web import kp2027_bm_rpt_aligned as bm

REVIEW = Path(__file__).resolve().parents[1] / "audits/rph_5p_bm_kp2027_batch01_content_release_review_20261128.json"
FLAG = "CIKGULAJU_BM_KP2027_5P_ENABLED"
PHASES = {"engagement", "exploration", "explanation", "elaboration", "evaluation"}

def _load_batch(path, expected):
    from web.kp2027_bm_5p import companions
    data = json.loads(path.read_text(encoding="utf-8"))
    rows = data["records"]
    if len(rows) != len(expected) or data.get("total") != len(expected):
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
    if set(result) != expected:
        raise bm.Unavailable("Senarai semakan 5P tidak lengkap")
    return result

# Independently validate each batch. A malformed unreleased batch cannot
# remove the previously approved first batch from the live catalogue.
BATCH_RANGES = ((1,12,12),(13,28,28),(29,60,60),(61,100,100),(101,178,175))

def _batch(number):
    start, end_a, end_b = BATCH_RANGES[number-1]
    expected = {(g,n) for g,end in (("A",end_a),("B",end_b))
                for n in range(start,end+1)}
    path = REVIEW.with_name(f"rph_5p_bm_kp2027_batch{number:02d}_content_release_review_20261128.json")
    return _load_batch(path,expected)

@lru_cache(maxsize=1)
def reviewed_records():
    result = {}
    for number in range(1,6):
        result.update(_batch(number))
    if len(result) != 353:
        raise bm.Unavailable("Inventori semakan penuh tidak lengkap")
    return result

@lru_cache(maxsize=1)
def publication_records():
    # Keep first batch independently validated; later batches fail closed.
    result = _batch(1)
    for number in range(2,6):
        try:
            result.update(_batch(number))
        except (OSError,ValueError,TypeError,KeyError,ImportError,AttributeError):
            continue
    return result

def released_groups():
    result = {"A": [], "B": []}
    if os.environ.get(FLAG) != "1":
        return result
    try:
        rows = publication_records()
        for (g,n), row in rows.items():
            if row.get("ready") is True and row.get("status") == "APPROVED_FOR_RELEASE":
                result[g].append(n)
        return {g: sorted(ns) for g,ns in result.items()}
    except (OSError, ValueError, TypeError, KeyError, ImportError, AttributeError):
        return {"A": [], "B": []}

def is_released(g,n):
    return type(n) is int and isinstance(g,str) and n in released_groups().get(g, [])

def reviewed_phases(g,n):
    return dict(publication_records()[g,n]["proposed_phases"])
