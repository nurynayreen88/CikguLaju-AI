"""Source-bounded audit of 77 Year-2 textbook page-range notes.

An editor inspected the project's 2017 KSSR Semakan Year-2 textbook scan:
  Drive file: 1VDXKCAyEveZCkhMLVVIyl3qg2sZhk9KP
  PDF: 149 pages. Table of contents on PDF pages 5-6.
  Final visible numbered *content* page: 138 (PDF page 148);
  PDF page 149 is back cover.

The CI audit itself does not retrieve the copyrighted source PDF.
TOC range consistency is NOT proof that a specific Lesson maps to a
specific exercise/page, nor proof of rights to distribute the book.
"""
from __future__ import annotations
import argparse
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path
import re

from pi_quality_audit import ROOT, UNVERIFIED_PAGE

# Page starts observed on original book's two-page printed TOC.
STARTS = (1, 7, 13, 19, 25, 31, 37, 43, 49, 55, 61, 67,
          73, 79, 85, 91, 97, 103, 109, 115, 121, 127, 133)
LAST_PRINTED_CONTENT_PAGE = 138
PDF_PAGES = 149
SOURCE_DRIVE_ID = "1VDXKCAyEveZCkhMLVVIyl3qg2sZhk9KP"
PAGE_RE = re.compile(r"ms\.\s*(\d+)\s*[–—-]\s*(\d+)")
BAD_END_IDS = {"T2-L102", "T2-L105", "T2-L108"}
CSV_FIELDS = (
    "id", "source_note", "source_note_sha256",
    "claimed_start", "claimed_end", "toc_corroborated_start",
    "toc_bounded_end", "claimed_range_matches_toc_bounds",
    "claimed_end_beyond_visible_printed_book", "requires_editor_range_fix",
    "specific_sp_and_page_verified", "direct_book_page_activity_verified",
    "copyright_permission_to_distribute", "content_expert_approved",
    "can_publish", "release"
)


def bounded_end(start):
    if start not in STARTS:
        raise ValueError("Unrecognized chapter start")
    index = STARTS.index(start)
    return STARTS[index + 1] - 1 if index + 1 < len(STARTS) else LAST_PRINTED_CONTENT_PAGE


def audit(root=ROOT):
    data = json.loads((Path(root) / "year2.json").read_text(encoding="utf-8"))
    assert data["year"] == 2 and data["ready"] is False and len(data["records"]) == 112
    rows = []
    for record in data["records"]:
        if record["withheld"]:
            continue
        src = record["fields"]["bahan"]
        notes = "\n".join(src.splitlines()[1:])
        if not any(x in notes.casefold() for x in UNVERIFIED_PAGE):
            continue
        match = PAGE_RE.search(notes)
        if not match:
            raise ValueError("Source page claim not parsed: " + record["id"])
        start, end = map(int, match.groups())
        if start not in STARTS:
            raise ValueError("Unknown book chapter start: " + record["id"])
        # A Jawi note can span three consecutive TOC units (37-54).
        eligible_starts = [s for s in STARTS if start <= s <= end]
        assert eligible_starts[0] == start
        expected_end = bounded_end(eligible_starts[-1])
        exceeds = end > LAST_PRINTED_CONTENT_PAGE
        needs_fix = end != expected_end
        if needs_fix and record["id"] not in BAD_END_IDS:
            raise ValueError("Unreviewed TOC range mismatch: " + record["id"])
        if record["id"] in BAD_END_IDS:
            evidence = record.get("staging_textbook_toc_correction")
            assert evidence is not None
            assert evidence["original_note_preserved"] is True
            assert evidence["original_claimed_printed_pages"] == [133, 140]
            assert evidence["proposed_section_range_for_editor"] == [133, 138]
            assert evidence["source_drive_file_id"] == SOURCE_DRIVE_ID
            assert evidence["last_visible_printed_content_page"] == LAST_PRINTED_CONTENT_PAGE
            assert evidence["sp_to_specific_page_verified"] is False
            assert evidence["content_expert_approved"] is False
            assert evidence["publication"] == "HOLD"
        rows.append({
            "id": record["id"],
            "source_note": notes,
            "source_note_sha256": hashlib.sha256(notes.encode("utf-8")).hexdigest(),
            "claimed_start": start,
            "claimed_end": end,
            "toc_corroborated_start": start,
            "toc_bounded_end": expected_end,
            "claimed_range_matches_toc_bounds": not needs_fix,
            "claimed_end_beyond_visible_printed_book": exceeds,
            "requires_editor_range_fix": needs_fix,
            "specific_sp_and_page_verified": False,
            "direct_book_page_activity_verified": False,
            "copyright_permission_to_distribute": False,
            "content_expert_approved": False,
            "can_publish": False,
            "release": "NO_GO",
        })
    assert len(rows) == 77
    assert len({x["id"] for x in rows}) == 77
    assert {x["id"] for x in rows if x["requires_editor_range_fix"]} == BAD_END_IDS
    assert sum(x["claimed_range_matches_toc_bounds"] for x in rows) == 74
    assert len(set(x["source_note"] for x in rows)) == 18
    by_start = Counter(x["claimed_start"] for x in rows)
    return {
        "purpose": "2017 textbook original TOC correlation, editorial metadata only",
        "source_drive_id": SOURCE_DRIVE_ID,
        "source_book": "Buku Teks Pendidikan Islam Tahun 2 KSSR Semakan (2017)",
        "book_source_pdf_total_pages": PDF_PAGES,
        "source_toc_pdf_pages_observed": [5, 6],
        "final_visible_numbered_content_pdf_page": 148,
        "final_visible_printed_page": LAST_PRINTED_CONTENT_PAGE,
        "source_book_read_again_in_ci": False,
        "source_toc_range_evidence_type": "editor visual inspection",
        "notes_checked": len(rows),
        "distinct_source_notes": 18,
        "ranges_consistent_with_toc_starts": 74,
        "out_of_book_end_page_claims": len(BAD_END_IDS),
        "out_of_book_end_lesson_ids": sorted(BAD_END_IDS),
        "specific_lesson_page_verified": 0,
        "corrections_approved": 0,
        "by_claimed_start": dict(sorted(by_start.items())),
        "academic_quality_percent": None,
        "can_publish": False,
        "release": "NO_GO",
        "rows": rows,
    }


def write(json_path, csv_path, root=ROOT):
    result = audit(root)
    Path(json_path).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n",
                               encoding="utf-8")
    with Path(csv_path).open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(result["rows"])
    print(json.dumps({k: v for k, v in result.items() if k != "rows"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--json", required=True)
    p.add_argument("--csv", required=True)
    args = p.parse_args()
    write(args.json, args.csv)
