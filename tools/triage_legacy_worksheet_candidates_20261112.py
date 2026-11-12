"""Deterministic read-only triage of CikguLaju historic worksheet candidates.

No migration or template publishing. This distinguishes 4,316 worksheet
blueprints from 20,332 curriculum combinations and physical printables.
Only aggregate counts and bounded static teaching-content examples are emitted.
"""
import json
import re
import sqlite3
from pathlib import Path
from urllib.parse import quote
from collections import Counter

WORKSHEET_DB = "CikguLaju_Worksheet_Content.db"
RESOURCE_DB = "CikguLaju_Templates_08.db"
DELIVERY_DB = "CikguLaju_Templates_09.db"
VISUAL_DB = "CikguLaju_Visuals_06.db"
REVIEW_DB = "CikguLaju_Curriculum_Master_v24_95_MATERIAL_AUDIT.db"
ALLOWLIST = (WORKSHEET_DB, RESOURCE_DB, DELIVERY_DB, VISUAL_DB, REVIEW_DB)
MAX_SAMPLE_TEXT = 135


def _connect(root, filename):
    if filename not in ALLOWLIST:
        raise ValueError("Source not allowlisted")
    path = Path(root).resolve() / filename
    if not path.is_file() or path.is_symlink() or path.stat().st_size > 80 * 1024 * 1024:
        raise FileNotFoundError("Read-only source not accessible")
    uri = "file:" + quote(str(path.resolve()), safe="/") + "?mode=ro&immutable=1"
    con = sqlite3.connect(uri, uri=True, timeout=2)
    con.execute("PRAGMA query_only=ON")
    return con


def _distribution(conn, table, col, limit=24):
    # Caller owns table/column identifiers; never interpolate user input here.
    rows = conn.execute(
        "SELECT COALESCE(CAST(" + col + " AS TEXT),'NULL'), COUNT(*) "
        "FROM " + table + " GROUP BY 1 ORDER BY COUNT(*) DESC, 1 LIMIT ?", (limit,)
    ).fetchall()
    return [{"value": str(value)[:96], "count": count} for value, count in rows]


def _clean(value):
    # Educational source snippets ONLY. No database files, keys or user records.
    val = re.sub(r"\s+", " ", str(value or "")).strip()
    return val[:MAX_SAMPLE_TEXT]


def audit(root):
    report = {
        "classification": "INTERNAL_REVIEW_ONLY",
        "production_worksheet_gate": "OFF",
        "approved_for_release": 0,
        "counts_are_records_not_final_worksheets": True,
    }
    with _connect(root, WORKSHEET_DB) as db:
        blueprint = db.execute("SELECT COUNT(*) FROM worksheet_blueprints").fetchone()[0]
        templates = db.execute("SELECT COUNT(*) FROM worksheet_item_templates").fetchone()[0]
        report["worksheet_blueprint_count"] = blueprint
        report["item_template_count"] = templates
        report["blueprint_year_subject"] = [
            {"year_label": _clean(y), "subject": _clean(s), "count": n}
            for y, s, n in db.execute(
                "SELECT year_label, subject, COUNT(*) FROM worksheet_blueprints "
                "GROUP BY year_label, subject ORDER BY year_label, subject"
            ).fetchall()
        ]
        report["alignment_blueprints"] = _distribution(
            db, "worksheet_blueprints", "verified_alignment")
        report["alignment_item_templates"] = _distribution(
            db, "worksheet_item_templates", "verified_alignment")
        report["completeness"] = dict(zip(
            ["missing_title", "missing_instructions", "missing_question_pattern",
             "missing_answer_space", "missing_sk", "missing_sp"],
            db.execute("""
                SELECT
                  SUM(CASE WHEN TRIM(COALESCE(title,''))='' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN TRIM(COALESCE(instructions,''))='' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN TRIM(COALESCE(question_pattern,''))='' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN TRIM(COALESCE(answer_space,''))='' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN TRIM(COALESCE(sk_code,''))='' THEN 1 ELSE 0 END),
                  SUM(CASE WHEN TRIM(COALESCE(sp_code,''))='' THEN 1 ELSE 0 END)
                FROM worksheet_blueprints
            """).fetchone()
        ))
        report["distinct_blueprint_keys"] = db.execute(
            "SELECT COUNT(DISTINCT blueprint_key) FROM worksheet_blueprints"
        ).fetchone()[0]
        report["distinct_item_template_keys"] = db.execute(
            "SELECT COUNT(DISTINCT template_key) FROM worksheet_item_templates"
        ).fetchone()[0]
        report["item_type_distribution"] = _distribution(
            db, "worksheet_item_templates", "item_type")
        report["year_label_distribution"] = _distribution(
            db, "worksheet_blueprints", "year_label")
        # Bounded static teaching content; never a learner/teacher account table.
        sample = db.execute("""
            SELECT year_label,subject,sk_code,sp_code,title,instructions,
                   question_pattern,answer_space,verified_alignment
            FROM worksheet_blueprints
            WHERE year_label IS NOT NULL AND subject IS NOT NULL
            ORDER BY year_label,subject,id
        """).fetchall()
        chosen, used = [], set()
        for row in sample:
            group = (str(row[0]), str(row[1]))
            if group in used:
                continue
            used.add(group)
            chosen.append({
                "year": _clean(row[0]), "subject": _clean(row[1]),
                "sk": _clean(row[2]), "sp": _clean(row[3]),
                "title": _clean(row[4]), "instructions": _clean(row[5]),
                "question_pattern": _clean(row[6]),
                "answer_space": _clean(row[7]),
                "alignment_raw": _clean(row[8]),
                "status": "SAMPLE_NOT_APPROVED"
            })
            if len(chosen) >= 14:
                break
        report["review_samples"] = chosen
    with _connect(root, RESOURCE_DB) as db:
        report["shared_resource_records"] = db.execute(
            "SELECT COUNT(*) FROM shared_learning_resource_v2397").fetchone()[0]
        report["resource_verification"] = _distribution(
            db, "shared_learning_resource_v2397", "verification_status")
        report["resource_worksheet_flag"] = _distribution(
            db, "shared_learning_resource_v2397", "reusable_by_worksheet")
    with _connect(root, DELIVERY_DB) as db:
        report["delivery_records"] = db.execute(
            "SELECT COUNT(*) FROM bbm_material_delivery_v23101").fetchone()[0]
        report["delivery_release_status"] = _distribution(
            db, "bbm_material_delivery_v23101", "release_status")
    with _connect(root, VISUAL_DB) as db:
        report["visual_asset_records"] = db.execute(
            "SELECT COUNT(*) FROM visual_assets").fetchone()[0]
        report["visual_approval"] = _distribution(db, "visual_assets", "approved")
        report["visual_min_dimensions"] = db.execute(
            "SELECT MIN(width_px), MIN(height_px) FROM visual_assets").fetchone()
    with _connect(root, REVIEW_DB) as db:
        report["curriculum_review_queue_records"] = db.execute(
            "SELECT COUNT(*) FROM lesson_material_review_queue_v2419").fetchone()[0]
        report["curriculum_review_decisions"] = _distribution(
            db, "lesson_material_review_queue_v2419", "decision")
    return report


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--root", default=".")
    p.add_argument("--out", required=True)
    args = p.parse_args()
    data = audit(Path(args.root))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    print("LEGACY_WORKSHEET_TRIAGE: status", data["classification"],
          "approved", data["approved_for_release"])
    for name in (
        "worksheet_blueprint_count", "item_template_count",
        "distinct_blueprint_keys", "distinct_item_template_keys",
        "completeness", "alignment_blueprints", "alignment_item_templates",
        "item_type_distribution", "resource_verification", "resource_worksheet_flag",
        "delivery_release_status", "visual_asset_records", "visual_approval",
        "curriculum_review_queue_records", "curriculum_review_decisions",
    ):
        print(name, json.dumps(data[name], ensure_ascii=False))
    print("YEAR_SUBJECT", json.dumps(data["blueprint_year_subject"], ensure_ascii=False))
    print("SAMPLE_METADATA", json.dumps(data["review_samples"], ensure_ascii=False))


if __name__ == "__main__":
    main()
