"""Audit use of Buku Aktiviti Pendidikan Islam without fabricating page/exercise links.

Standalone staging-only ledger. This module never edits a RPH, DB, or runtime.
External school resource pages identify candidate editions but do NOT establish
that a specific PDF, exercise, page, or re-distribution licence was verified.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import argparse
import json
import re

from pi_quality_audit import COUNT, HELD, ROOT

# Public school resource discovery pages, NOT approved download artifacts.
SCHOOL_RESOURCES = (
    "https://sites.google.com/moe-dl.edu.my/panitiapendidikanislamtldmkk/buku-teks",
    "https://sites.google.com/moe-dl.edu.my/lamanbestaripdpc/sumber-bahan/buku-teks-buku-aktiviti",
)
KPM_POLICY = "https://www.moe.gov.my/index.php/list-page/497"
BOOK_MENTION_RE = re.compile(
    r"buku\\s*(?:aktiviti|kerja)|activity\\s*book|workbook|"
    r"بوکو\\s*اکتيۏيتي|بوكو\\s*اكتيؤيتي",
    flags=re.IGNORECASE,
)
TASMI_RE = re.compile(r"ختم\\s*القرءان|تسميع\\s*القرءان|جزء\\s*\\d+", re.UNICODE)

# The official school sources list BA for standard Tahun 1-3. This workflow
# covers Year 2-6; Tahun 1 KP2027 is not silently mixed into older syllabus.
def audit_activity_books(root=ROOT):
    rows = []
    for year, expected in COUNT.items():
        payload = json.loads((Path(root)/f"year{year}.json").read_text(encoding="utf-8"))
        assert len(payload["records"]) == expected and payload["ready"] is False
        for lesson, record in enumerate(payload["records"], 1):
            assert record["lesson"] == lesson and record["tahun"] == year
            key = (year, lesson)
            if key in HELD:
                assert record["withheld"] is True
                rows.append({
                    "id": record["id"], "year": year,
                    "disposition": "WITHHELD",
                    "page": None, "exercise": None, "verified": False,
                    "activity_book_reference_in_rph": False,
                })
                continue
            assert record["withheld"] is False
            fields = record["fields"]
            body = "\\n".join(value for value in fields.values() if isinstance(value, str))
            mentions = bool(BOOK_MENTION_RE.search(body))
            domain_match = re.search(
                r"Bidang:\\s*([^\\s•]+)", " ".join(record.get("intro", []))
            )
            domain = domain_match.group(1) if domain_match else None
            sp = fields["sp"]
            tasmi = bool(TASMI_RE.search(fields["sk"] + "\\n" + sp))
            if year in (2, 3):
                disposition = (
                    "MUSHAF_PRIMARY_NO_ASSUMED_BA"
                    if tasmi else "REVIEW_FOR_EXERCISE_MATCH"
                )
                source_state = "EXTERNAL_EDITION_SEEN_NOT_OWNED_OR_PAGE_VERIFIED"
                book_name = f"Buku Aktiviti Pendidikan Islam Tahun {year} KSSR Semakan"
                source_urls = list(SCHOOL_RESOURCES)
            else:
                disposition = "NO_STANDARD_BOOK_CONFIRMED_FOR_YEAR"
                source_state = "NOT_IDENTIFIED"
                book_name = None
                source_urls = []
            rows.append({
                "id": record["id"],
                "year": year,
                "domain": domain,
                "source_sp": sp,
                "disposition": disposition,
                "book_title_candidate": book_name,
                "book_source_state": source_state,
                "source_urls": source_urls,
                "activity_book_reference_in_rph": mentions,
                "page": None,
                "exercise": None,
                "verified": False,
                "can_show_to_teacher": False,
                "can_download_from_cikgulaju": False,
                "source_page_matches_sp": False,
                "licence_verified_for_distribution": False,
                "review_instruction": (
                    "Match topic, exercise and print page in a legally usable actual edition "
                    "to DSKP SP and lesson before adding ONE purposeful sentence to RPH."
                    if disposition == "REVIEW_FOR_EXERCISE_MATCH"
                    else "Retain Quran/mushaf tasmi' as core; do not force an invented workbook "
                    "page." if tasmi
                    else "No standard BA established for Year 4-6; do not invent pages."
                ),
            })
    assert len(rows) == 696
    status = Counter(r["disposition"] for r in rows)
    mentions = sum(r["activity_book_reference_in_rph"] for r in rows)
    return {
        "subject": "Pendidikan Islam",
        "scope": "2027 staging Years 2-6",
        "reviewed_records": 696,
        "open_drafts": 690,
        "withheld": 6,
        "year2_year3_active_drafts": sum(
            r["year"] in (2,3) and r["disposition"] != "WITHHELD" for r in rows
        ),
        "mapping_candidates": status["REVIEW_FOR_EXERCISE_MATCH"],
        "quran_tasmi_no_forced_workbook": status["MUSHAF_PRIMARY_NO_ASSUMED_BA"],
        "year4_year6_no_book_confirmed": status["NO_STANDARD_BOOK_CONFIRMED_FOR_YEAR"],
        "book_mentions": mentions,
        "verified_exercise_links": 0,
        "disposition_counts": dict(status),
        "approval_state": "HOLD_NOT_READY",
        "distribution": "DO_NOT_COPY_EXTERNAL_PDFS_WITHOUT_RIGHTS",
        "rows": rows,
    }


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--output", required=True)
    args = p.parse_args()
    r = audit_activity_books()
    Path(args.output).write_text(
        json.dumps(r, ensure_ascii=False, indent=2) + "\\n", encoding="utf-8"
    )
    print(json.dumps({k:v for k,v in r.items() if k!="rows"}, ensure_ascii=False, indent=2))
