"""Consolidate repeated Rumi closing passages for safe human Jawi review.

Never autotransliterates, edits RPH, or approves teaching content. Exact-source
grouping reduces 690 per-lesson reviews to a smaller set of distinct passages.
"""
from __future__ import annotations
import argparse
from collections import defaultdict
import csv
import hashlib
import json
from pathlib import Path
import re

from pi_quality_audit import ROOT, COUNT, HELD

HEADERS = (
    "group_id", "lesson_count", "lesson_ids", "years", "domain_labels",
    "original_closing_rumi", "original_text_sha256",
    "approved_jawi_text", "academic_reviewer", "jawi_reviewer",
    "source_checked", "word_pdf_verified", "can_publish", "release"
)


def build(root=ROOT):
    groups = defaultdict(list)
    for year, expected in COUNT.items():
        source = json.loads((Path(root) / f"year{year}.json").read_text(encoding="utf-8"))
        assert len(source["records"]) == expected
        for record in source["records"]:
            if (year, record["lesson"]) in HELD:
                assert "fields" not in record
                continue
            text = record["fields"]["penutup"]
            assert text.strip()
            groups[text].append({
                "id": record["id"],
                "year": year,
                "intro": " ".join(record.get("intro", [])),
            })
    result = []
    for index, (closing, group) in enumerate(
        sorted(groups.items(), key=lambda pair: (-len(pair[1]), pair[0])),
        start=1
    ):
        years = sorted({r["year"] for r in group})
        domains = sorted({
            match.group(1) if (match := re.search(r"Bidang:\s*([^\s•]+)", r["intro"]))
            else "unknown"
            for r in group
        })
        result.append({
            "group_id": f"PI-CLOSING-{index:03d}",
            "lesson_count": len(group),
            "lesson_ids": "|".join(r["id"] for r in group),
            "years": "|".join(str(y) for y in years),
            "domain_labels": "|".join(domains),
            "original_closing_rumi": closing,
            "original_text_sha256": hashlib.sha256(closing.encode("utf-8")).hexdigest(),
            "approved_jawi_text": None,
            "academic_reviewer": None,
            "jawi_reviewer": None,
            "source_checked": False,
            "word_pdf_verified": False,
            "can_publish": False,
            "release": "NO_GO",
        })
    assert sum(r["lesson_count"] for r in result) == 690
    assert len({item for r in result for item in r["lesson_ids"].split("|")}) == 690
    assert all(re.search("[A-Za-z]", r["original_closing_rumi"]) for r in result)
    return {
        "purpose": "Human-only Jawi script consistency and closure content review",
        "lesson_count": 690,
        "unique_closings": len(result),
        "all_source_text_preserved": True,
        "jawi_replacements_approved": 0,
        "academic_quality_certified": False,
        "can_publish": False,
        "release": "NO_GO",
        "groups": result,
    }


def write(root, json_output, csv_output):
    result = build(root)
    Path(json_output).write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    with Path(csv_output).open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=HEADERS)
        writer.writeheader()
        writer.writerows(result["groups"])
    print(json.dumps({k: v for k, v in result.items() if k != "groups"},
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", required=True)
    parser.add_argument("--csv", required=True)
    args = parser.parse_args()
    write(ROOT, args.json, args.csv)
