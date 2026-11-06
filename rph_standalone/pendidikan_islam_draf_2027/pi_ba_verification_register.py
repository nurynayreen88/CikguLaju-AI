"""Editor verification register for 174 BA candidates (T2/3, KSSR Semakan).

The 42 page hints are SECONDARY teacher-resource leads only. None is a
direct inspection of the actual activity-book exercise. This file does not
write RPH, publish third-party book files or claim teacher-facing approval.

Outputs UTF-8-SIG CSV for reviewing in Excel and a machine-readable JSON
audit for CI. Official book codes verified in KPM e-Catalog 2023.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import csv
import json

from pi_ba_match_queue import NEEDS_PAGE, match_queue
from pi_ba_secondary_evidence import evidence_queue
from pi_ba_source_integrity import EXPECTED

COLUMNS = [
    "lesson_id", "year", "book_code_KPM", "domain", "sp_codes",
    "learning_focus", "secondary_source_count", "secondary_reported_pages",
    "secondary_source_url", "secondary_source_topic", "secondary_conflict",
    "needs_direct_book_inspection", "original_book_printed_page",
    "original_exercise_number", "original_exercise_instruction_summary",
    "page_image_hash_sha256", "evidence_internal_reference",
    "exercise_matches_sp_reviewed_by", "jawi_language_approved_by",
    "teacher_sentence_after_verified", "a4_word_pdf_verified",
    "status", "can_publish", "can_redistribute_book_pdf"
]


def register():
    all_candidates = [
        r for r in match_queue()["rows"] if r["disposition"] == NEEDS_PAGE
    ]
    hints = evidence_queue()["rows"]
    by_id = {}
    for item in hints:
        by_id.setdefault(item["lesson_id"], []).append(item)
    assert len(hints) == 42
    assert len(by_id) == 42

    rows = []
    for item in all_candidates:
        year = item["year"]
        book = EXPECTED[year]
        pages = by_id.get(item["id"], [])
        joined = sorted({p for h in pages
                         for p in h["page_numbers_reported_by_secondary_source"]})
        sources = sorted({h["secondary_source_url"] for h in pages})
        conflicts = any(h.get("cross_source_conflict_detected", False)
                        for h in pages)
        row = {
            "lesson_id": item["id"], "year": year,
            "book_code_KPM": book["kpm_catalog_code"],
            "domain": item["domain"],
            "sp_codes": ", ".join(item["sp_codes"]),
            "learning_focus": item["learning_focus"],
            "secondary_source_count": len(pages),
            "secondary_reported_pages": ", ".join(map(str, joined)),
            "secondary_source_url": " | ".join(sources),
            "secondary_source_topic": " | ".join(
                h["topic_correspondence"] for h in pages
            ),
            "secondary_conflict": conflicts,
            "needs_direct_book_inspection": True,
            "original_book_printed_page": "",
            "original_exercise_number": "",
            "original_exercise_instruction_summary": "",
            "page_image_hash_sha256": "",
            "evidence_internal_reference": "",
            "exercise_matches_sp_reviewed_by": "",
            "jawi_language_approved_by": "",
            "teacher_sentence_after_verified": "",
            "a4_word_pdf_verified": False,
            "status": "HOLD_AWAITING_ORIGINAL",
            "can_publish": False,
            "can_redistribute_book_pdf": False,
        }
        rows.append(row)

    counts = Counter(r["year"] for r in rows)
    candidates_with_hints = sum(bool(r["secondary_source_count"]) for r in rows)
    conflicts = [r["lesson_id"] for r in rows if r["secondary_conflict"]]
    assert counts == {2: 76, 3: 98}, counts
    assert candidates_with_hints == 42
    assert len(rows) == 174 and len({r["lesson_id"] for r in rows}) == 174
    assert conflicts == ["T3-L004"]
    assert all(not r["original_book_printed_page"] and not r["can_publish"]
               for r in rows)
    return {
        "subject": "Pendidikan Islam",
        "book_codes": {str(k): EXPECTED[k]["kpm_catalog_code"] for k in (2,3)},
        "scope": "174 BA exercise candidates for editor-only verification",
        "lesson_count": len(rows),
        "year_counts": dict(counts),
        "secondary_hint_count": candidates_with_hints,
        "without_secondary_hints": len(rows) - candidates_with_hints,
        "contradiction_count": len(conflicts),
        "contradicted_lesson_ids": conflicts,
        "direct_book_pages_verified": 0,
        "exercise_instructions_verified": 0,
        "RPH_with_BA_pages_updated": 0,
        "release": "NO_GO",
        "rows": rows,
    }


def save_csv(path, data):
    with open(path, "w", encoding="utf-8-sig", newline="") as out:
        writer = csv.DictWriter(out, fieldnames=COLUMNS, extrasaction="raise")
        writer.writeheader()
        # Escaping prevents spreadsheet-formula injection from untrusted metadata.
        for row in data["rows"]:
            safe = {}
            for k in COLUMNS:
                value = row[k]
                if isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                    value = "'" + value
                safe[k] = value
            writer.writerow(safe)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--csv", required=True)
    a = p.parse_args()
    data = register()
    Path(a.json).write_text(json.dumps(data, ensure_ascii=False, indent=2)+"\n",
                            encoding="utf-8")
    save_csv(a.csv, data)
    print(json.dumps({k: v for k,v in data.items() if k!="rows"},
                     ensure_ascii=False, indent=2))
