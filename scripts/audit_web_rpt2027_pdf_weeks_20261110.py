"""Read-only audit: week numbers and Week 01 in the 56 *actual Web* RPT PDFs.

This never changes the original PDF bytes, manifest, curriculum sequence, or
teacher records. PDF text extraction is only a diagnostic, not a calendar or
academic approval. In particular, do NOT add weeks to a PDF from assumptions.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "rpt_2027" / "web_2027_pdfs"
OUT = ROOT / "output" / "rpt2027_week_audit_20261110.json"

# Two-way extraction catches Latin LTR M01 and M 01. RTL PDF text extraction
# may reverse M01 as 10M; report mirrored matches separately for review.
NORMAL = re.compile(r"(?<![\w])M\s*0?([1-9]|[1-3][0-9]|4[0-4])(?![\w])", re.I)
MIRRORED = re.compile(r"(?<![\w])([0-9]{1,2})M(?![\w])", re.I)
DATE = re.compile(r"(?<!\d)\d{2}/\d{2}/2027(?!\d)")


def weeks_in_text(source):
    out = set()
    for match in NORMAL.finditer(source):
        out.add(int(match.group(1)))
    for match in MIRRORED.finditer(source):
        reverse = match.group(1)[::-1]
        if reverse.isdigit() and 1 <= int(reverse) <= 44:
            out.add(int(reverse))
    return sorted(out)


def audit():
    import fitz  # install only in isolated CI, not Web production runtime

    manifest = json.loads((CATALOG / "manifest.json").read_text("utf-8"))
    files = manifest["files"]
    if len(files) != 56 or manifest.get("count") != 56:
        raise ValueError("Web RPT2027 manifest is not the expected 56-file catalog")

    results = []
    for identity, entry in sorted(files.items()):
        path = CATALOG / entry["path"]
        data = path.read_bytes()
        if len(data) != entry["bytes"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
            raise ValueError(f"{identity}: production PDF bytes/SHA mismatch")
        with fitz.open(stream=data, filetype="pdf") as doc:
            if len(doc) != entry["pages"]:
                raise ValueError(f"{identity}: manifest page count mismatch")
            text_by_page = [page.get_text("text", sort=True) for page in doc]
        labels = sorted({n for page in text_by_page for n in weeks_in_text(page)})
        first_week_pages = [i for i, page in enumerate(text_by_page, 1)
                            if 1 in weeks_in_text(page)]
        dated_pages = sum(bool(DATE.search(page)) for page in text_by_page)
        results.append({
            "subject_year": identity,
            "pages": entry["pages"],
            "week_labels_found": labels,
            "number_of_distinct_weeks": len(labels),
            "has_week_01": bool(first_week_pages),
            "week_01_pdf_pages": first_week_pages[:6],
            "pages_with_printed_2027_dates": dated_pages,
            "no_week_label_in_extracted_text": not bool(labels),
            "pdf_sha256": entry["sha256"],
        })
        print("WEEK_CHECK", identity, "distinct_weeks=", len(labels),
              "M01=", bool(first_week_pages), "dated_pages=", dated_pages,
              "first=", labels[:3], "last=", labels[-3:], flush=True)

    by_subject = {}
    for item in results:
        subject = item["subject_year"].split(":")[0]
        count = by_subject.setdefault(subject, Counter())
        count["files"] += 1
        count["no_week_labels"] += int(item["no_week_label_in_extracted_text"])
        count["without_week_01"] += int(not item["has_week_01"])
    report = {
        "scope": "Web production SHA-verified 56 PDF snapshots, text extraction only",
        "source": "rpt_2027/web_2027_pdfs/manifest.json",
        "academic_signoff": False,
        "calendar_week_01_from_school_opening": "2027-01-04",
        "counts": {
            "total_files": len(results),
            "no_week_labels": sum(x["no_week_label_in_extracted_text"] for x in results),
            "without_week_01": sum(not x["has_week_01"] for x in results),
        },
        "by_subject": {subject: dict(count) for subject, count in sorted(by_subject.items())},
        "files": results,
        "notes": [
            "No week number may mean source week was never assigned, not visual clipping.",
            "Week-01 presence does not prove Week-01 contains a numbered PdP.",
            "An unassigned week must not be fabricated or represented as academically approved.",
            "PDF native Arabic/Jawi text extraction may omit or reorder glyphs; confirm visually.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("RPT_56_WEEK_AUDIT_SUMMARY=" + json.dumps(
        {"counts": report["counts"], "by_subject": report["by_subject"]},
        ensure_ascii=False, sort_keys=True))
    return report


if __name__ == "__main__":
    audit()
