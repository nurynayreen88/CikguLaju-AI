"""Editor-only audit of 13 ambiguous 'Buku Aktiviti' mentions in Year-5 Jawi RPH.

A reference to a classroom workbook is not automatically evidence of an official
KPM activity-book edition, page or exercise. Do NOT add a download or workbook
page, convert Jawi, rewrite the source RPH, or publish these candidates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re

from pi_quality_audit import COUNT, HELD, ROOT

TERM = re.compile(r"بوكو\s+اكتيۏيتي")
EXPECTED = {
    "T5-L092": "pentaksiran",
    "T5-L096": "pentaksiran",
    "T5-L100": "pentaksiran",
    "T5-L104": "pentaksiran",
    "T5-L111": "pentaksiran",
    "T5-L115": "pentaksiran",
    "T5-L119": "pentaksiran",
    "T5-L123": "pentaksiran",
    "T5-L127": "pentaksiran",
    "T5-L131": "aktiviti_utama",
    "T5-L135": "aktiviti_utama",
    "T5-L139": "aktiviti_utama",
    "T5-L143": "aktiviti_utama",
}


def audit(root=ROOT):
    root = Path(root)
    rows = []
    for year, expected in COUNT.items():
        records = json.loads((root / f"year{year}.json").read_text(encoding="utf-8"))["records"]
        assert len(records) == expected
        for lesson in records:
            if (year, lesson["lesson"]) in HELD:
                assert lesson["withheld"] and "fields" not in lesson
                continue
            assert not lesson["withheld"] and lesson["verified_ready"] is False
            matches = []
            for field, content in lesson["fields"].items():
                for match in TERM.finditer(content):
                    matches.append((field, content, match))
            if not matches:
                continue
            assert len(matches) == 1, ("Unexpected multiple activity-book mentions", lesson["id"])
            field, content, match = matches[0]
            assert year in (4, 5, 6), ("Review any newly observed Y2/Y3 workbook reference separately", lesson["id"])
            left = max(0, match.start()-70)
            right = min(len(content), match.end()+100)
            rows.append({
                "id": lesson["id"],
                "year": year,
                "field": field,
                "source_wording": match.group(),
                "source_excerpt": content[left:right],
                "original_field_sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
                "official_book_edition_verified": False,
                "official_book_page_verified": False,
                "official_exercise_verified": False,
                "could_be_generic_activity_workbook": True,
                "editor_next_step": (
                    "Semak buku asal dan maksud istilah: buku kerja umum atau Buku Aktiviti "
                    "rasmi? Jika rasmi, rekod edisi, muka surat bercetak dan latihan SP; "
                    "jika buku kerja umum, jelaskan arahan dalam draf selepas semakan Jawi."
                ),
                "original_rph_changed": False,
                "review_only": True,
                "can_publish": False,
                "release": "NO_GO",
            })
    found = {row["id"]: row["field"] for row in rows}
    assert len(rows) == len(EXPECTED) and found == EXPECTED, (
        "Exact source citations changed; investigate, do not silently approve", found
    )
    assert all(not x["can_publish"] and not x["official_book_page_verified"] for x in rows)
    return {
        "scope": "Pendidikan Islam Tahun 2-6, existing source RPH; mentions confined to Tahun 5",
        "subject": "Pendidikan Islam",
        "total_lesson_catalog": 696,
        "source_mentions_reviewed": len(rows),
        "year5_pentaksiran_mentions": sum(x["field"] == "pentaksiran" for x in rows),
        "year5_activity_mentions": sum(x["field"] == "aktiviti_utama" for x in rows),
        "official_year5_buku_aktiviti_pages_verified_by_this_audit": 0,
        "official_year5_buku_aktiviti_exercises_verified_by_this_audit": 0,
        "original_rph_edits": 0,
        "reviewed_by_subject_expert": False,
        "academic_quality_percent": None,
        "status": "EDITOR_REVIEW_PENDING",
        "release": "NO_GO",
        "rows": rows,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    opts = parser.parse_args()
    result = audit()
    Path(opts.output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, ensure_ascii=False, indent=2))
