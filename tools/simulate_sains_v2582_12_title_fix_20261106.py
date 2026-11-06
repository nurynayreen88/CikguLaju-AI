"""Simulate v25.82 Sains Y3 12 verified-DSKP title repairs in throwaway DB.

This tool must NEVER write to shipped part files or production. The transaction
is always rolled back and the temporary copy is deleted. All 385 Sains rows are
checked field-for-field after simulation.
"""
from __future__ import annotations
import json, sqlite3, tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
LEDGER=ROOT/"audits/sains_y3_v2582_12_dskp_title_corrections_20261106.json"
STEM="CikguLaju_Curriculum_Master_v25_82_PRIMARY_LANGUAGE_SCIENCE_VERB_QA.db"

def simulate():
    ledger=json.loads(LEDGER.read_text("utf-8"))
    fixes=ledger["changes"]
    if ledger["source_checkpoint"]!="v25.82 PRIMARY_LANGUAGE_SCIENCE_VERB_QA":
        raise ValueError("Wrong source checkpoint")
    if len(fixes)!=12 or len({x["pdp_code"] for x in fixes})!=12:
        raise ValueError("Expected 12 unique proposals")
    with tempfile.TemporaryDirectory(prefix="cikgulaju_sains_v2582_title_") as td:
        dbpath=Path(td)/"SCIENCE_EDIT_SIMULATION_ONLY.db"
        parts=[ROOT/(STEM+f".part{i}") for i in (1,2)]
        if not all(p.is_file() for p in parts):raise FileNotFoundError("v25.82 parts missing")
        with dbpath.open("wb") as dst:
            for part in parts:
                with part.open("rb") as src:
                    for block in iter(lambda:src.read(1024*1024),b""):
                        dst.write(block)
        with sqlite3.connect(dbpath) as db:
            db.row_factory=sqlite3.Row
            if db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
                raise ValueError("v25.82 integrity failed")
            original={r["id"]:dict(r) for r in db.execute(
                "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")}
            if len(original)!=385:raise ValueError("Unexpected historical Sains count")
            db.execute("BEGIN IMMEDIATE")
            try:
                for x in fixes:
                    n=db.execute("""
                        UPDATE verified_pdp_sequence SET pdp_title=?
                        WHERE year_label='Tahun 3' AND subject='Sains'
                          AND pdp_sequence_code=? AND source_sequence_no=?
                          AND sk_code=? AND sp_code=? AND pdp_title=?
                    """,(x["ds_kpm_official_sp_text"],x["pdp_code"],
                         x["source_sequence_no"],x["sk_code"],x["sp_code"],
                         x["original_title"])).rowcount
                    if n!=1:raise ValueError("Source changed since ledger "+x["pdp_code"])
                modified={r["id"]:dict(r) for r in db.execute(
                    "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")}
                field_diffs={
                    k:{col for col in original[k] if original[k][col]!=modified[k][col]}
                    for k in original
                }
                field_diffs={k:v for k,v in field_diffs.items() if v}
                if len(field_diffs)!=12 or any(v!={"pdp_title"} for v in field_diffs.values()):
                    raise ValueError("Changed non-title rows/fields "+repr(field_diffs))
                after_count=len(modified)
            finally:
                db.rollback()
            restored={r["id"]:dict(r) for r in db.execute(
                "SELECT * FROM verified_pdp_sequence WHERE subject='Sains'")}
            if restored!=original or db.execute("PRAGMA quick_check").fetchone()[0]!="ok":
                raise RuntimeError("Rollback/integrity check failed")
    return {
        "status":"SIMULATION_PASS_NOT_APPROVED_FOR_DEPLOY",
        "source":"v25.82 working copy only",
        "proposed_updated_titles":12,
        "source_385_rows_unchanged_after_rollback":len(original),
        "temporary_only_fields_modified":["pdp_title"],
        "simulated_row_total":after_count,
        "rolled_back_and_deleted":True,
        "release_decision":"HOLD",
    }

if __name__=="__main__":
    print(json.dumps(simulate(),indent=2,ensure_ascii=False))
