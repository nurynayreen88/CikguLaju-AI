"""Evidence provenance for Buku Aktiviti, staging-only.

Separates teacher-supplied BA page references from the original book's
printed pages and exercises. No hint is eligible for runtime publication.
"""
from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path

from pi_ba_secondary_evidence import evidence_queue

SPECIAL_CONFLICT = "T3-L004"
PDPR_YEARS_2020_2021 = (
    "https://anyflip.com/rvse/yhcp/basic",
    "https://www.scribd.com/document/521518334/PENDIDIKAN-ISLAM-TAHUN-3",
)


def classify(item):
    url = item["secondary_source_url"]
    if item["lesson_id"] == SPECIAL_CONFLICT:
        label = "SECONDARY_CONFLICT_SOURCE_PAGES"
        review = ("Arahan PdPR Tahun 3 menyatakan p65-66 bagi Jawi imbuhan awalan "
                  "walaupun halaman sama turut dinyatakan bagi Akidah; "
                  "jangan menganggap p49-51 daripada video sebagai jawapan.")
    elif url in PDPR_YEARS_2020_2021:
        label = "TEACHER_PDPR_BOOK_ACTIVITY_PAGE_CLAIM"
        review = ("Dokumen PdPR guru menyebut halaman Buku Aktiviti; "
                  "padanan SP/latihan khusus belum disemak pada buku asal.")
    elif "youtube.com" in url:
        label = "VIDEO_PAGE_RANGE_UNCONFIRMED"
        review = ("Tajuk/julat halaman dilaporkan melalui penerangan video. "
                  "Tiada pemeriksaan halaman bercetak atau nombor latihan.")
    else:
        label = "OTHER_TEACHER_SOURCE_PAGE_CLAIM"
        review = ("Petunjuk daripada bahan PdPR pihak lain; pengesahan teks asal "
                  "halaman dan latihan masih diperlukan.")
    return {
        "lesson_id": item["lesson_id"],
        "source_url": url,
        "source_classification": label,
        "reported_pages": item["page_numbers_reported_by_secondary_source"],
        "conflict": item["cross_source_conflict_detected"],
        "recheck_note": review,
        "original_book_page_checked": False,
        "exercise_checked": False,
        "approved_rph_page": None,
        "allowed_to_publish": False,
    }


def provenance_report():
    a = evidence_queue()
    rows = [classify(x) for x in a["rows"]]
    counters = Counter(r["source_classification"] for r in rows)
    assert len(rows) == 42 and len({r["lesson_id"] for r in rows}) == 42
    assert counters == {
        "TEACHER_PDPR_BOOK_ACTIVITY_PAGE_CLAIM": 27,
        "VIDEO_PAGE_RANGE_UNCONFIRMED": 8,
        "OTHER_TEACHER_SOURCE_PAGE_CLAIM": 6,
        "SECONDARY_CONFLICT_SOURCE_PAGES": 1,
    }, counters
    assert all(not x["original_book_page_checked"] and
               x["approved_rph_page"] is None and
               not x["allowed_to_publish"] for x in rows)
    return {
        "subject": "Pendidikan Islam",
        "secondary_hints_total": len(rows),
        "source_classes": dict(sorted(counters.items())),
        "direct_workbook_page_verified": 0,
        "exercise_matched_to_sp_verified": 0,
        "publishable_page_references": 0,
        "status": "NO_GO_EDITOR_REVIEW_ONLY",
        "rows": rows,
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", required=True)
    args = ap.parse_args()
    data = provenance_report()
    Path(args.output).write_text(
        json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in data.items() if k != "rows"},
                     ensure_ascii=False, indent=2))
